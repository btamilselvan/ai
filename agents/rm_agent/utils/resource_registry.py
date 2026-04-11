from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from typing import Dict
from openai import OpenAI
from utils.rm_agent import RecipeManagerAgent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis
import logging
from utils.summarization_agent import SummarizationAgent

logger = logging.getLogger(__name__)


class ResourceRegistry():
    """ Registry for all resources. Registry will be stored in the FastAPI app state """
    redis_client: redis.Redis
    async_session: async_sessionmaker[AsyncSession]
    openai_client: OpenAI

    def __init__(self):
        # AsyncExitStack - a dynamic, asynchronous version of Try-with- in Java.
        self._stack = AsyncExitStack()
        self.mcp_sessions: Dict[str, ClientSession] = {}
        self.ai_clients: Dict[str, any] = {}
        self.tools_map: Dict[str, list] = {}
        self.toolname_servername_map: Dict[str, str] = {}

    def setup_redis_client(self, host='localhost', port=6379, db=0, max_connections=10):
        """ setup redis client and add to registry """
        pool = redis.ConnectionPool(
            host=host, port=port, db=db, max_connections=max_connections)
        self.redis_client = redis.Redis(connection_pool=pool)

    def create_database_engine(self, database_url):
        """ create database engine and add to registry """
        logger.info("creating database engine with url: %s", database_url)
        engine = create_async_engine(url=database_url, echo=False)
        async_session = async_sessionmaker(engine, expire_on_commit=False)
        self.async_session = async_session
        logger.info("database connection ...%s...", async_session)

    async def dispose_database_engine(self):
        """ dispose database engine """
        if self.async_session:
            engine = self.async_session.kw["bind"]
            await engine.dispose()

    async def setup_mcp_client(self, name, url):
        """ setup mcp client and add to registry """
        # logger.info(f"Setting up MCP client: {name} at {url}")
        read, write = await self._stack.enter_async_context(sse_client(url=url))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.mcp_sessions[name] = session

        logger.info("MCP client and sessions initialized: %s at %s", name, url)
        # load tools
        tools = await self.__load_tools(name, session)
        self.tools_map[name] = tools
        # logger.info("tools map %s", self.tools_map)

    async def __load_tools(self, server_name, session: ClientSession):
        """ load tools from mcp session """

        tools = await session.list_tools()

        all_tools = []

        for tool in tools:
            if isinstance(tool[1], list):
                # print(f"Multiple tools found: {tool[1]}")
                for t in tool[1]:
                    # print(f"Tool: {t}")
                    self.toolname_servername_map[t.name] = server_name
                    # open ai chat expects the tool format be in the below format
                    all_tools.append({
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema
                        }
                    })

        return all_tools

    def setup_openai_client(self, url, api_key):
        client = OpenAI(base_url=url, api_key=api_key)
        self.openai_client = client

    def setup_ai_client(self, name, client, model, tools: list = []):
        """ setup generic ai client and add to registry """
        if "main_agent" == name:
            rm_agent = RecipeManagerAgent(
                client=client, model=model, tools=tools)
            self.ai_clients[name] = rm_agent
        elif "summarization_agent" == name:
            summarization_agent = SummarizationAgent(
                client=client, model=model)
            self.ai_clients[name] = summarization_agent

        logger.info("AI clients initialized with tools: %s", tools)

    async def cleanup(self):
        """ cleanup all clients """
        await self._stack.aclose()
