from fastmcp import FastMCP
import json

# Initalize the server
mcp = FastMCP()

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


@mcp.tool
def recipe_search(query: str) -> list[dict]:
    """
    Search for recipes by title or ingredients. 
    Returns the top 5 matching IDs and Titles.
    """
    print(f"Searching for recipes matching: {query}")
    recipes = []
    for recipe in mock_recipes:
        if query.lower() in recipe["title"].lower() or query.lower() in recipe["ingredients"].lower():
            recipes.append({"id": recipe["id"], "title": recipe["title"]})
    return recipes

# resources return string response
@mcp.resource(uri="recipe://details/{id}")
def get_recipe_details(id: int) -> str:
    """
    Get the full details of a recipe by its ID.
    """
    print(f"Fetching details for recipe ID: {id}")
    
    for recipe in mock_recipes:
        if recipe["id"] == id:
            return json.dumps(recipe, indent=2)
    return "Recipe not found"


@mcp.resource(uri="recipe://docs/safety")
def get_safety_guidelines() -> str:
    """Mandatory kitchen safety protocols."""
    print("Fetching safety guidelines...")
    
    return """
    Safety Guidelines for Cooking:
    1. Always wash your hands before handling food.
    2. Keep raw and cooked foods separate to avoid cross-contamination.
    3. Cook foods to their recommended internal temperatures.
    4. Refrigerate perishable foods within two hours of cooking.
    5. Use clean utensils and surfaces when preparing food.
    """


@mcp.resource(uri="recipe://docs/measurements")
def get_measurements() -> str:
    """Common cooking measurements."""
    print("Fetching measurements...")
    return """
    Measurement Conversions:
    1 cup = 16 tablespoons = 48 teaspoons = 240 ml
    1 tablespoon = 3 teaspoons = 14.8 ml
    1 teaspoon = 4.9 ml
    1 ounce = 28.3 grams
    1 pound = 454 grams
    """


# run the server
if __name__ == "__main__":
    mcp.run(transport="stdio")
