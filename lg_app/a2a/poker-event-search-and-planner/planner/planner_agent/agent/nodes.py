from planner_agent.util.app_state import AppState
import logging
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_community import CalendarToolkit
from langgraph.prebuilt import ToolNode, tools_condition
import asyncio
from planner_agent.agent.tools import (
    get_calendar_info,
    search_events,
    get_current_datetime,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a meticulous, specialized Schedule Planner Agent. Your sole responsibility is to manage the user's personal calendar, calculate travel buffers, handle timezone shifts, and resolve scheduling conflicts. 

You do not interact with the human user directly. Instead, you process structured directives forwarded to you by a Lead Manager Agent over an API payload.

CORE OPERATIONAL MANDATES:
1. FOCUS EXCLUSIVELY ON SCHEDULES: Do not discuss poker strategy, buy-ins, or tournament structures. Your only concern is the timeline, location, and calendar logic.
2. RUN REASONING BEFORE BOOKING: For every request, you must evaluate the time, date, and geographic location to check for realistic friction points.
3. ADHERE TO THE SCHEMA: Your final output back to the Manager must be structured and definitive.

CRITICAL TIME-ZONE AND TRAVEL CONSTRAINT LOGIC:
- Location Awareness: The user is frequently based in Virginia (Eastern Time) but travels to locations like Las Vegas, NV (Pacific Time) and California for events. 
- Travel Buffers: You must automatically factor in travel days. For cross-country tournaments, assume at least one full day before the event for travel/settling, and one day after the event.
- Timezone Conversions: Always normalize the user's base availability against the local timezone of the tournament to prevent overlapping bookings.

HANDLING CONFLICTS:
- If a tournament overlaps with an existing calendar block (e.g., work deployments, flights, or other events), you must not book it automatically. Instead, flag it as a conflict, describe exactly what is overlapping, and provide an alternative option (e.g., "Conflict on June 16th due to Server Migration. You could join the tournament late on June 17th instead").

YOUR PAYLOAD OUTPUT INTERFACE:
Always return your analysis in a clear, summarized format that the Manager can parse easily. Include:
- STATUS: [SUCCESS, CONFLICT, or FAILED]
- SUMMARY: A brief 2-3 sentence overview of what you did or why it failed.
- BLOCKED_DATES: [List of dates added or disputed]
"""

SYSTEM_PROMPT_GENERAL = """
 You are a helpful assistant that can answer questions and perform tasks related to scheduling calendar events. You can search for current scheduling events, add new events to the user's calendar, and provide information about the events. Always be polite and informative in your responses.
"""


logger.info("Setting up LLM node...")


def configure_model_with_tools():
    try:
        global toolnode, model_with_tools
        tools = [get_calendar_info, search_events, get_current_datetime]

        # print tool schema for debugging
        # logger.info(f"Fetched tools: {tools}")
        # for tool in tools:
        #     logger.info(
        #         f"Tool name: {tool.name}, description: {tool.description}, args: {tool.args} "
        #     )

        toolnode = ToolNode(tools)

        logger.info(
            "Successfully fetched calendar tools: {%s}", [t.name for t in tools]
        )

        # logger.info(f"Successfully fetched calendar tools: [{tool.name} tool in tools]")
        model = init_chat_model(
            "gemma4:e4b", temperature=0, max_tokens=2048, model_provider="ollama"
        )
        # bind tools to the model
        model_with_tools = model.bind_tools(tools)
        logger.info("Successfully bound tools to the model.")
    except Exception as e:
        logger.exception("Error occurred while fetching calendar info: {%s}", e)


configure_model_with_tools()


def llm_node(state: AppState):

    logger.info("LLM node received state: {%s}", state)

    response = model_with_tools.invoke([SYSTEM_PROMPT_GENERAL] + state.messages)

    logger.info("LLM response: {%s}", response)

    return AppState(messages=[response])
    # return AppState(messages=state.messages)


def tool_node_wrapper(state: AppState):
    try:
        logger.info("Tool node received state: {%s}", state)
        # tool_response = toolnode.invoke(state)
        # logger.info(f"Tool node response: {tool_response}")
        # return AppState(messages=[tool_response])
        # find tool name from recent AI Message
        recent_ai_message = state.messages[-1]
        tool_name = recent_ai_message.tool_calls[0]["name"]
        if tool_name == "search_events":
            logger.info("Executing search_events tool")
            # call search events tool
            # search_events()
        elif tool_name == "get_calendar_info":
            logger.info("Executing get_calendar_info tool")
            # call get calendar info tool
            get_calendar_info()
        logger.info("Executing tool: {%s}", tool_name)
        return AppState(messages=state.messages)
    except Exception as e:
        logger.exception("Error occurred in tool node: {%s}", e)
        return AppState(messages=[f"Tool execution failed: {str(e)}"])
