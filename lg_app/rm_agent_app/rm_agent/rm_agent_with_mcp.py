import asyncio
from functools import partial
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from rm_agent.utils.state import RecipeAppState
from rm_agent.utils.nodes import llm_node, tool_node_wrapper, resource_router_node, conditional_edge, resource_node, rag_node
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

print("hello rm agent..")

# load environment variables
load_dotenv()

# System prompt
SYSTEM_PROMPT = """
# ROLE
You are the Professional Recipe Manager Assistant. Your goal is to help users discover, create, and audit recipes with high precision and safety.

# OPERATIONAL PROTOCOL (MCP)
1. **Discovery (Search)**: Use the `recipe_search` tool for any query involving recipe titles or ingredients. It returns the top 5 matches.
2. **Deep Dive (Resources)**: Once you have a recipe ID from a search, ALWAYS fetch the full content using the resource URI `recipe://details/{{id}}` before providing instructions.
3. **Safety First**: Before suggesting any cooking steps, reference kitchen safetey guidelines to ensure the instructions follow professional kitchen standards.
4. **Unit Consistency**: For all measurement conversions or scaling, reference the ground truth in measurement guide.

Use the provided context when answering questions about food safety, cooking techniques, or measurements.

# Context
{context}
"""

# initialize model
model = init_chat_model("deepseek-chat", temperature=0.5, max_tokens=2048)

# MCP client session has to be open throughout the agent interactions
mcp_client = MultiServerMCPClient({
    "rm_mcp_server": {
        "transport": "stdio",
        "command": "python",
        "args": [
            "/Users/tamil/tamil/git_repository/tamil/ai/mcp/rm-mcp-server/main.py"
        ]
    }
})

# initialize chromadb
embedding_function = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")
vector_store = Chroma(collection_name="rm_knowledge_collection",
                      persist_directory="/Users/tamil/tamil/git_repository/tamil/ai/lg_app/rm_agent_app/ingestion/chroma_db",
                      embedding_function=embedding_function)
retriever = vector_store.as_retriever(search_type="similarity")


async def get_resources() -> str:
    resources = await mcp_client.get_resources()

    resource_catalog = "\n".join(
        [f"URI: {resource.metadata['uri']}:\n Data: {resource.data}" for resource in resources])
    return resource_catalog


async def get_updated_system_prompt() -> str:
    await get_resources()
    return SYSTEM_PROMPT + "AVAILABLE RESOURCES:\n" + await get_resources()


async def run_it():
    tools = await mcp_client.get_tools()
    print(f"Available MCP tools: {tools}")

    resources = await mcp_client.get_resources()
    # print resource uri
    # formatted_strings = [f"{resource}" for resource in resources]

    resources_dict = {}

    for resource in resources:
        resources_dict[str(resource.metadata['uri'])] = resource.data

    print("Available MCP server resources:", resources_dict)

    # print("Available MCP server resources:", formatted_strings)

    print("Running Recipe Manager Agent...")

    # map the tool name to the correspodning tool definition
    # tool_by_name = {tool.name.lower(): tool for tool in tools}

    model_with_tools = model.bind_tools(tools)
    mcp_tool_node = ToolNode(tools)

    # updated_system_prompt = await get_updated_system_prompt()

    updated_system_prompt = SYSTEM_PROMPT
    print(f"updated system prompt {updated_system_prompt}")

    # Define a simple graph
    workflow = StateGraph(RecipeAppState)
    workflow.add_node("rag", partial(rag_node, retriever=retriever))
    workflow.add_node("llm", partial(
        llm_node, model_with_tools=model_with_tools, system_prompt=updated_system_prompt))
    workflow.add_node("tools", partial(
        tool_node_wrapper, mcp_tool_node=mcp_tool_node))
    # workflow.add_node("resources", partial(
    #     resource_router_node, resources_dict=resources_dict))

    # workflow.add_node("resources", partial(
    #     resource_node, mcp_client=mcp_client))
    workflow.set_entry_point("rag")
    workflow.add_edge("rag", "llm")
    # workflow.set_entry_point("llm")
    workflow.add_conditional_edges("llm", tools_condition)
    # workflow.add_conditional_edges("llm", conditional_edge, {
    #                                "tools": "tools", "resources": "resources", "END": END})
    workflow.add_edge("tools", "llm")
    # workflow.add_edge("resources", "llm")

    graph = workflow.compile()
    print(graph.get_graph().draw_ascii())

    return graph

agent = asyncio.run(run_it())
