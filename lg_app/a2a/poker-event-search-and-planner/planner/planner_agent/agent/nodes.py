from planner_agent.util.app_state import AppState
import logging
import json
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, AIMessage, ToolCall
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_community import CalendarToolkit
from langgraph.prebuilt import ToolNode, tools_condition
from redis import Redis
from typing import List
from planner_agent.agent.tools import (
    get_calendars_info,
    search_events,
    get_current_datetime,
)
from planner_agent.util.google_resources import (
    get_calendar_info as google_calendar_info,
    get_current_datetime as google_calendar_datetime,
    search_events as google_search_events,
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
 Make sure to send tool call arguments in the format expected by the tool.
"""


logger.info("Setting up LLM node...")


def configure_model_with_tools():
    try:
        global toolnode, model_with_tools
        tools = [get_calendars_info, search_events, get_current_datetime]

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

    # logger.info("LLM node received state: {%s}", state)

    response = model_with_tools.invoke([SYSTEM_PROMPT_GENERAL] + state.messages)

    logger.info("LLM response: {%s}", response)

    return AppState(messages=[response], thread_id=state.thread_id, email=state.email)


def tool_node_wrapper(state: AppState, r: Redis):
    # logger.info("Tool node received state: {%s}", state)

    # find tool name from recent AI Message
    recent_ai_message: AIMessage = state.messages[-1]

    for tool_call in recent_ai_message.tool_calls:
        # logger.info("Processing tool call: {%s}", tool_call)
        state = __execute_tool_call(tool_call, state, r)

    return state

def __execute_tool_call(tool_call: ToolCall, state: AppState, r: Redis):
    tool_name = tool_call["name"]
    tool_call_id = tool_call["id"]
    logger.info("Executing tool call: {%s}", tool_call)

    try:
        if tool_name == "search_events":
            logger.info("Executing search_events tool")
            args = tool_call.get("args", {})
            tool_response = google_search_events(
                state.email,
                r,
                args.get("min_datetime"),
                args.get("max_datetime"),
                args.get("single_events", True),
                args.get("", None),
            )
        elif tool_name == "get_calendars_info":
            logger.info("Executing get_calendars_info tool....")
            tool_response = google_calendar_info(state.email, r)
        elif tool_name == "get_current_datetime":
            logger.info("Executing get_current_datetime tool")
            tool_response = google_calendar_datetime(state.email, r)
        else:
            logger.error("Unknown tool name: {%s}", tool_name)
            tool_response = (
                f"Unknown tool name: {tool_name}, tool_call_id: {tool_call_id}"
            )

        logger.info("Tool response: {%s}", tool_response)

        if tool_response:
            tool_message = ToolMessage(
                content=json.dumps(tool_response), tool_call_id=tool_call_id
            )
            state.messages = [tool_message]
        else:
            logger.warning("No tool response generated")
            state.messages = [
                ToolMessage(
                    content="Tool executed but no response generated",
                    tool_call_id=tool_call_id,
                )
            ]
        return state

    except Exception as e:
        logger.exception("Error occurred in tool execution: {%s}", e)
        state.messages = [
            ToolMessage(
                content=f"Tool execution failed: {str(e)}",
                tool_call_id=tool_call_id,
            )
        ]
        return state
