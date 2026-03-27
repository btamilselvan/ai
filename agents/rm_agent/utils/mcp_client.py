# not used
import os
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from mcp.client import sse
from mcp import ClientSession
from dotenv import load_dotenv
# from mcp_tools import McpTools

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/sse")

# @asynccontextmanager
async def create_mcp_client(app: FastAPI):
    print("server startup initiated...")
    async with sse.sse_client(url=MCP_SERVER_URL) as (read, write):
        print("Connected to MCP server")
        async with ClientSession(read, write) as session:
            print("Connected to MCP session")
            await session.initialize()
            app.state.rm_mcp_session = session
            # load tools
            # mcp_tools.
            
            yield

            print("server shutdown initiated...")
            print("mcp client and session closed...")

# async def li