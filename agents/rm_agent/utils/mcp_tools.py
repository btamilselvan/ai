# not used
from mcp import ClientSession
from typing import List
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
import json

class McpTools():
    def __init__(self, client_session: ClientSession):
        self.client_session = client_session

    async def list_tools(self):

        print(f"Retrieving available tools from session {self.client_session}")
        tools = await self.client_session.list_tools()

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
    
    def build_tools_map(self, tool_calls_map: dict, tool_calls: List[ChoiceDeltaToolCall]):
        # print(f"dict {tool_calls_map}, {tool_calls}")
        for index, tool_call in enumerate(tool_calls):
            print(f"Tool call: {tool_call[1]}")
            ## if function_name is not None
            # tool call ID
            if tool_call[1].id:
                print(f"Tool call ID: {tool_call[1].id}")
            # tool name
            
            # tool argouments
            
            
            if(index not in tool_calls_map):
                tool_calls_map[index] = {
                    
                }
            
            if(tool_call[1].id):
                tool_calls_map[tool_call[1].id] = tool_call[1].function.name
            if(tool_call[1].function):
                print(f"Function name: {tool_call[1].function.name}")
            

    async def execute_tool(self, tool_call):
        print(f"Executing tool call: {tool_call.id}")
        arguments = json.loads(tool_call.function.arguments)
        tool_response = await self.client_session.call_tool(name=tool_call.function.name, arguments=arguments)
        print(f"tool_response {tool_response}")
