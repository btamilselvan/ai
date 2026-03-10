import asyncio
from functools import partial
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import tools_condition
from rm_agent.utils.tools import mock_recipe_search, get_resources
from rm_agent.utils.state import RecipeAppState
from rm_agent.utils.nodes import llm_node, tool_node

print("hello rm agent..")

# load environment variables
load_dotenv()

# System prompt
SYSTEM_PROMPT = """
# ROLE
You are the Professional Recipe Manager Assistant. Your goal is to help users discover, create, and audit recipes with high precision and safety.

# OPERATIONAL PROTOCOL (MCP)
1. **Discovery (Search)**: Use the `search_recipes` tool for any query involving recipe titles or ingredients. It returns the top 5 matches.
2. **Deep Dive (Resources)**: Once you have a recipe ID from a search, ALWAYS fetch the full content using the resource URI `recipe://details/{id}` before providing instructions.
3. **Safety First**: Before suggesting any cooking steps, reference `recipe://docs/safety` to ensure the instructions follow professional kitchen standards.
4. **Unit Consistency**: For all measurement conversions or scaling, reference the ground truth in `recipe://docs/measurements`.

# TOOL SPECIFICATIONS
- `search_recipes(query: str)`: 
    - Input: Recipe title, single ingredient, or a comma-separated list of ingredients.
    - Output: A list of the top 5 matching recipes (including ID and Title).

# CONSTRAINTS
- Do not summarize a recipe based only on its title; always read the full Resource.
- If no recipes are found via `search_recipes`, suggest alternative ingredients or ask the user if they would like to create a new recipe.
- Maintain a professional, structured, and helpful English-speaking persona.

# SAFETY
If a user suggests a technique that contradicts `recipe://docs/safety`, politely correct them and provide the safe alternative found in the resource.
"""

# initialize model
model = init_chat_model("deepseek-chat", temperature=0.5, max_tokens=2048)


async def run_it():
    print("Running Recipe Manager Agent...")
    tools = [mock_recipe_search, get_resources]
    # map the tool name to the correspodning tool definition
    tool_by_name = {tool.name.lower(): tool for tool in tools}
    
    model_with_tools = model.bind_tools(tools)

    # Define a simple graph
    workflow = StateGraph(RecipeAppState)
    # workflow.add_node("llm", )
    workflow.add_node("llm", partial(
        llm_node, model_with_tools=model_with_tools, system_prompt=SYSTEM_PROMPT))
    workflow.add_node("tools", partial(tool_node, tool_by_name=tool_by_name))

    workflow.set_entry_point("llm")
    workflow.add_conditional_edges("llm", tools_condition)
    workflow.add_edge("tools", "llm")

    graph = workflow.compile()
    print(graph.get_graph().draw_ascii())

    return graph


agent = asyncio.run(run_it())
