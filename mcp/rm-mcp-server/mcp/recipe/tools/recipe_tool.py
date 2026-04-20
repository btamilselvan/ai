from fastmcp.tools import tool
from fastmcp.dependencies import CurrentRequest
from fastmcp import Context
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)


mock_recipes = [
    {"id": 10966, "title": "Avocado Toast",
        "ingredients": "Bread, Avocado, Lemon juice, Salt, Black pepper, Chili flakes"},
    {"id": 10973, "title": "Butter Chicken",
        "ingredients": "Chicken, Butter, Tomato puree, Cream, Garam masala, Garlic, Ginger"},
    {"id": 11513, "title": "Coconut Shrimp with Pasta",
        "ingredients": "Shrimp, Pasta, Onions, Garlic, Olive oil, Salt, Pepper"},
    {"id": 11005, "title": "French Toast",
        "ingredients": "Bread, Eggs, Milk, Cinnamon"},
    {"id": 12005, "title": "Spicy Paneer with Rice and Kale",
        "ingredients": "Paneer, Rice, Kale, Green Beans, Garlic, Olive oil, Salt, Pepper, Fresh herbs"}
]


# Note the @tool decorator from factmcp.tools.tool instead of @mcp.tool - this is to avoid the circular dependency
# when mcp server instance is imported from server.py. FileSystemProvider is smart to identify the tool usign @tool annotation
@tool(name="search")
async def recipe_search(query: str, context: Context, request: Request = CurrentRequest()) -> list[dict]:
    """
    Search for recipes by title or ingredients. 
    Returns the top 5 matching IDs and Titles.
    Returns an empty list if no recipes match.
    """

    logger.debug("Request Headers: %s", request.headers)

    logger.debug("Searching for recipes matching: %s", query)

    await context.report_progress(25, 100, "Searching recipes...")

    # await asyncio.sleep(5)

    await context.info(f"fetching recipes matching for query {query}")

    last_search_query = await context.get_state("last_search_query")
    if last_search_query:
        logger.debug("Previous search query was: %s", last_search_query)

    await context.set_state("last_search_query", query)

    recipes = []
    for recipe in mock_recipes:
        if query.lower() in recipe["title"].lower() or query.lower() in recipe["ingredients"].lower():
            recipes.append({"id": recipe["id"], "title": recipe["title"]})
    return recipes


@tool("recipes")
def get_recipe_details(recipe_id: int) -> dict:
    """
    Get the full details of a recipe by its ID.
    """
    logger.debug("Fetching details for recipe ID: %d", recipe_id)

    for recipe in mock_recipes:
        if recipe["id"] == recipe_id:
            return recipe
    return {"error": f"Recipe with ID {recipe_id} not found."}
