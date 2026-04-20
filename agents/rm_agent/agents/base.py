import asyncio
import logging
from openai import OpenAI
import json
from utils.models import AppState, ConversationModel, ToolCall, ToolFunctionInfo
from typing import Dict
from fastmcp import Client

logger = logging.getLogger(__name__)


class BaseAgent:
    def __init__(self, client: OpenAI, model, toolname_servername_map, temperature=0.7, tools: list = None, max_tokens=4096):
        logger.info("RM agent initialized...")
        self.client = client
        self.model = model
        self.toolname_servername_map = toolname_servername_map
        self.temperature = temperature
        self.tools = tools
        self.max_tokens = max_tokens

    async def __tool_call_progress_handler(self, progress: float, total: float | None, message: str | None):
        """ handle tool call progress """

        # emit the tool call progress to the client (UI) - TODO
        if total is not None:
            percentage = (progress / total) * 100
            logger.info("Progresss %.1f - %s ", percentage, message or '')
        else:
            logger.info("Progresss %.1f - %s ", progress, message or '')

    def __collect_tool_calls(self, response):
        if response.choices and response.choices[0].message.tool_calls:
            tool_calls: list[ToolCall] = []
            for tool_call in response.choices[0].message.tool_calls:

                tool_calls.append(ToolCall(type=tool_call.type,
                                           id=tool_call.id,
                                           function=ToolFunctionInfo(
                                               name=tool_call.function.name,
                                               arguments=tool_call.function.arguments
                                           )))
            return tool_calls

        return None

    async def __invoke_tool(self, mcp_client: Client, tool: ToolCall, thread_id):
        tool_response = await mcp_client.call_tool(tool.function.name, json.loads(tool.function.arguments), meta={
            "thread_id": thread_id}, progress_handler=self.__tool_call_progress_handler)
        logger.debug("tool response: %s", tool_response)

        tool_response_content_text = tool_response.content[0].text if tool_response.content else ""

        # add tool response to the messages to be sent back to the LLM for the next iteration of the loop
        # return {"role": "tool", "content": tool_response_content_text, "tool_calls": [tool], "tool_call_id": tool.id}
        return ConversationModel(
            thread_id=thread_id,
            role="tool",
            content=tool_response_content_text,
            tool_calls=[tool],
            tool_call_id=tool.id)

    def __convert_llm_response_to_model(self, response) -> ConversationModel:

        logger.debug("tool calls %s", self.__collect_tool_calls(response))

        conv_model = ConversationModel(
            role="assistant",
            content=response.choices[0].message.content,
            tool_calls=self.__collect_tool_calls(response)
        )

        return conv_model

    def invoke_llm(self, context: str, appstate: AppState) -> AppState:
        """ call the LLM with the context and the user message """

        prompt = self.SYSTEM_PROMPT.format(context=context)

        # add system prompt at index 0
        messages = [
            {"role": "system", "content": prompt}
        ] + [msg.model_dump(exclude={"thread_id", "summary", "id", "created_at"}) for msg in appstate.messages]

        logger.debug("calling LLM with messages: %s", messages)

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=messages,
                # stream=True,
                tools=self.tools,
            )
            # for chunk in response:
            #     yield chunk
            logger.debug("LLM response received: %s",
                         response.choices[0].message)
            conv_model = self.__convert_llm_response_to_model(response)
            conv_model.thread_id = appstate.thread_id

            appstate.messages.append(conv_model)
            return appstate
        except Exception as e:
            print(f"An error occurred: {e}")
            # retry??
            raise
            # return None

    async def execute_tool_calls(self, toolname_servername_map: Dict[str, str], mcp_client_map, appstate: AppState) -> AppState:
        """ execute the tool calls returned by the LLM concurrently """

        logger.debug("executing tool calls...")

        async def invoke(tool: ToolCall):
            logger.info("executing tool call: %s", tool)
            server_name = toolname_servername_map.get(tool.function.name)
            mcp_client: Client = mcp_client_map.get(server_name)
            return await self.__invoke_tool(mcp_client, tool, appstate.thread_id)

        tool_responses = await asyncio.gather(
            *[invoke(tool) for tool in appstate.messages[-1].tool_calls]
        )

        appstate.messages.extend(tool_responses)
        return appstate
