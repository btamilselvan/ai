# not used

import os
from mcp.client.sse import sse_client
from mcp import ClientSession


async def get_available_tools(session: ClientSession):
    print(f"Retrieving available tools from session {session}")
    tools = await session.list_tools()

    all_tools = []

    for tool in tools:
        if isinstance(tool[1], list):
            print(f"Multiple tools found: {tool[1]}")
            for t in tool[1]:
                # print(f"Tool: {t}")
                # open ai chat expects the tool format be in the below format
                all_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                })
                print(t)
    print(f"Total tools: {all_tools}")
    return all_tools
