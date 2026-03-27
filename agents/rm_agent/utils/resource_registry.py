from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client
from typing import Dict
from openai import OpenAI
from utils.rm_agent import RecipeManagerAgent


class ResourceRegistry():
    """ Registry for all resources. Registry will be stored in the FastAPI app state """

    def __init__(self):
        # AsyncExitStack - a dynamic, asynchronous version of Try-with- in Java.
        self._stack = AsyncExitStack()
        self.mcp_sessions: Dict[str, ClientSession] = {}
        self.ai_clients: Dict[str, any] = {}
        self.openai_client: OpenAI
        self.tools_map: Dict[str, list] = {}
        self.toolname_servername_map: Dict[str, str] = {}

    async def setup_mcp_client(self, name, url):
        """ setup mcp client and add to registry """
        # print(f"Setting up MCP client: {name} at {url}")
        read, write = await self._stack.enter_async_context(sse_client(url=url))
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.mcp_sessions[name] = session

        print(f"MCP client and sessions initialized: {name} at {url}")
        # load tools
        tools = await self.__load_tools(name, session)
        self.tools_map[name] = tools
        # print(f"tools map {self.tools_map}")

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
            rm__agent = RecipeManagerAgent(
                client=client, model=model, tools=tools)
            self.ai_clients[name] = rm__agent

        print(f"AI client initialized with tools: {tools}")

    async def cleanup(self):
        """ cleanup all clients """
        await self._stack.aclose()
