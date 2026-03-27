# not used
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "recipe_search",
            "description": "Search recipes by keyword",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recipe_details",
            "description": "Get recipe details by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {"type": "integer"}
                },
                "required": ["recipe_id"]
            }
        }
    }
]
