from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from typing import Dict
from openai import OpenAI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis
import logging
from agents.summarization_agent import SummarizationAgent
from agents.supervisor import SupervisorAgent
from fastmcp import Client
from fastmcp.client.transports import SSETransport
from mcp.types import Tool

logger = logging.getLogger(__name__)


class ResourceRegistry():
    """ Registry for all resources. Registry will be stored in the FastAPI app state """
    redis_client: redis.Redis
    async_session: async_sessionmaker[AsyncSession]
    openai_client: OpenAI

    def __init__(self):
        # AsyncExitStack - a dynamic, asynchronous version of Try-with- in Java.
        self._stack = AsyncExitStack()
        # self.mcp_sessions: Dict[str, ClientSession] = {}
        self.mcp_clients: Dict[str, Client] = {}
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

    async def setup_mcp_client(self, name, url, api_key):
        """ setup mcp client and add to registry """
        # logger.info(f"Setting up MCP client: {name} at {url}")

        sse = SSETransport(url=url, headers={"x-api-key": api_key})
        client = Client(transport=sse)
        await self._stack.enter_async_context(client)
        # await client.ping()

        tools = await self.__load_tools(name, client)
        logger.info("Tools loaded from %s: %s", name, tools)
        self.tools_map[name] = tools
        self.mcp_clients[name] = client

        # read, write = await self._stack.enter_async_context(sse_client(url=url, headers={"x-api-key": api_key}))
        # session = await self._stack.enter_async_context(ClientSession(read, write))
        # await session.initialize()
        # self.mcp_sessions[name] = session

        logger.info("MCP client and sessions initialized: %s at %s", name, url)
        # load tools
        # tools = await self.__load_tools(name, session)
        # self.tools_map[name] = tools
        # logger.info("tools map %s", self.tools_map)

    async def __load_tools(self, server_name, client: Client):
        """ load tools from mcp session """

        tools: list[Tool] = await client.list_tools()

        all_tools = []

        for tool in tools:

            self.toolname_servername_map[tool.name] = server_name
            all_tools.append({
                "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
            })

        return all_tools

    def setup_openai_client(self, url, api_key):
        client = OpenAI(base_url=url, api_key=api_key)
        self.openai_client = client

    def setup_ai_client(self, name, client, model, tools: list = []):
        """ setup generic ai client and add to registry """
        if "supervisor_agent" == name:
            rm_agent = SupervisorAgent(
                client=client, model=model, tools=tools, toolname_servername_map=self.toolname_servername_map)
            self.ai_clients[name] = rm_agent
        elif "summarization_agent" == name:
            summarization_agent = SummarizationAgent(
                client=client, model=model, toolname_servername_map={})
            self.ai_clients[name] = summarization_agent

        logger.info("AI clients initialized with tools: %s", tools)

    async def cleanup(self):
        """ cleanup all clients """
        await self._stack.aclose()
