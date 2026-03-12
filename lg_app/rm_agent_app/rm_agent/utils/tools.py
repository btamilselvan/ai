from rm_agent.utils.state import RecipeAppState
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
# from langchain.to

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


def get_safety_guidelines() -> str:
    """Standard kitchen and appliance safety protocols."""
    return """
    # Kitchen Safety Guidelines
    1. **Knife Safety**: Always cut away from your body.
    2. **Heat**: Never leave a stove unattended. 
    3. **Sanitation**: Wash hands for 20 seconds before handling food.
    4. **Appliance Care**: Unplug appliances before cleaning.
    """


def get_measurements() -> str:
    """Standard culinary unit conversions."""
    return """
    | Unit | Equivalent |
    | :--- | :--- |
    | 1 cup | 240 ml |
    | 1 tablespoon | 15 ml |
    | 1 teaspoon | 5 ml |
    | 16 tablespoons | 1 cup |
    """


def get_recipe_by_id(recipe_id: int):
    """Fetch full recipe details by ID."""
    for recipe in mock_recipes:
        if recipe["id"] == recipe_id:
            return recipe
    return f"Recipe details Not found for recipe ID {recipe_id}"


@tool
def get_resources(resource_uri: str) -> str:
    """Fetch resources like safety guidelines or measurements."""

    print(f"Fetching resource: {resource_uri}")

    if "safety" in resource_uri:
        return get_safety_guidelines()
    elif "measurements" in resource_uri:
        return get_measurements()
    elif "details" in resource_uri:
        recipe_id = resource_uri.split("/")[-1]
        return get_recipe_by_id(int(recipe_id))
    else:
        return "Resource not found."


@tool
def mock_recipe_search(query: str) -> list[dict]:
    """Mock recipe search tool."""
    print(f"Searching for recipes with query: {query}")
    result = []
    for recipe in mock_recipes:
        if query.lower() in recipe["title"].lower() or query.lower() in recipe["ingredients"].lower():
            result.append(recipe)
    return result
