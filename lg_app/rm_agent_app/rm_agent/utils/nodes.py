from rm_agent.utils.state import RecipeAppState
from langgraph.prebuilt import ToolNode
from langchain.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.types import Command
from typing import Literal
from langchain_core.vectorstores import VectorStoreRetriever
import re

"""
e.g. message format (when tested via langgraph UI)

{
    "assistant_id": "rm_agent",
    "input": {
        "messages": [
            {
                "type": "human",
                "content": [
                    {
                        "text": "Can you suggest a couple of mouth watering peanut butter recipes?",
                        "type": "text"
                    }
                ]
            }
        ]
    },
    "stream_mode": "updates"
}

"""
def rag_node(state: RecipeAppState, retriever: VectorStoreRetriever) -> RecipeAppState:
    print("entering RAG Node..")
    last_message = state.get("messages", [])[-1]
    print(f"Last message {last_message}")
    print(f"Last message {((last_message["content"][0])["text"])}")
    content = ((last_message["content"][0])["text"])
    # content = last_message.content
    print(f"content {content}")
    docs = retriever.invoke(content)
    context = "\n".join(doc.page_content for doc in docs) if docs else ""
    print(f"Context: {context}")
    return RecipeAppState(context=context)


def llm_node(state: RecipeAppState, model_with_tools, system_prompt: str) -> RecipeAppState:
    print(f"Entering LLM node {len(state.get("messages", []))}")

    # print(f"system prompt {system_prompt}, context {state.get("context", "")}")

    updated_system_prompt = system_prompt.format(
        context=state.get("context", ""))

    messages = state.get("messages", []).copy()

    last_message = state.get("messages", [])[-1]
    print(f"Last message {last_message}")
    # print(f"Messages {messages}")
    message = model_with_tools.invoke(
        [SystemMessage(content=updated_system_prompt)] + messages)
    return RecipeAppState(messages=[message])


def tool_node(state: RecipeAppState, tool_by_name: dict) -> Command[Literal["llm"]]:
    print(f"Entering Tool node {len(state.get("messages", []))}")

    last_message = state.get("messages", [])[-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        print("No tool calls found in the last message.")
        return state

    tool_result = []
    try:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            args = tool_call["args"]
            print(f"Tool name: {tool_name}")
            print(f"Args: {args}")

            tool_response = tool_by_name.get(tool_name).invoke(args)

            tool_result.append(ToolMessage(content=str(
                tool_response), tool_call_id=tool_call["id"]))

        return Command(update={"messages": tool_result}, goto="llm")
    except Exception as e:
        print(f"Error executing tools: {e}")
        tool_result.append(ToolMessage(
            content=f"Tool error occurred {str(e)}", tool_call_id=tool_call["id"]))
        return Command(update={"messages": tool_result}, goto="llm")


async def tool_node_wrapper(state: RecipeAppState, mcp_tool_node: ToolNode) -> RecipeAppState:
    print(f"Entering Tool node wrapper {state}")
    result = await mcp_tool_node.ainvoke(state)
    print(f"Remote tool node result: {result}")
    return result


async def resource_node(state: RecipeAppState, mcp_client: MultiServerMCPClient) -> RecipeAppState:
    """Fetch resource content by URI."""

    print("execute resource node...")

    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None

    print(f"last message {last_message}")

    try:
        if "recipe://details" in last_message.content:

            pattern = r"recipe://details/(\d+)"

            matches = re.finditer(pattern, last_message.content)
            matches = list(matches)

            if (len(matches) > 0):
                resource_uri = matches[0].group(0)

                print(f"Fetching resource: {resource_uri}")

                resource_content = await mcp_client.get_resources(uris=resource_uri)

                resource_data = "NOT FOUND"

                if len(resource_content) > 0:
                    resource_data = resource_content[0].data

                print(f"Resource content: {resource_content[0]}")
                return RecipeAppState(messages=[SystemMessage(content=f"Resource Data from {resource_uri}: {resource_data}")])

        return RecipeAppState(messages=[SystemMessage(content="No resource required")])
    except Exception as e:
        print(f"Error fetching resource {resource_uri}: {e}")
        return RecipeAppState(messages=[SystemMessage(content=f"Error fetching data for resource {resource_uri}")])


def resource_router_node(state: RecipeAppState, resources_dict: dict):
    """
    Specialized node that detects if the LLM mentioned a URI and fetches the content from the MCP Resource registry.
    """
    print("Entering resource router node")
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None

    print(f"last message {last_message}")

    if "recipe://" in last_message.content:

        pattern = r"recipe://.*?(?=`)"
        matches = re.findall(pattern, last_message.content)

        for uri in matches:
            print(f"uri {uri}")
            if uri in resources_dict:
                content = resources_dict[uri]
                print(f"content {content}")
            return RecipeAppState(messages=[SystemMessage(content=f"Resource Data from {uri}: {content}")])

    return RecipeAppState(messages=[SystemMessage(content="I can't find the recipe you're referring to.")])


def conditional_edge(state: RecipeAppState) -> Literal["tools", "resources", "END"]:
    """ Decide whether to call the tool or not. """

    print("execute conditional edge \n")

    messages = state.get("messages", [])
    last_message = messages[-1] if messages else "END"

    print(f"last message {last_message}")

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    elif isinstance(last_message, AIMessage) and "recipe://details" in last_message.content:
        return "resources"
    else:
        return "END"
