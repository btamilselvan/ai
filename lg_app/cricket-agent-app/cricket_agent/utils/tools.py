from langchain.tools import tool, ToolRuntime
from langgraph.types import Command
from dataclasses import dataclass
from langchain.messages import ToolMessage

@tool("get_upcoming_matches")
def get_upcoming_matches():
    """ Fetches the upcoming cricket matches. """
    return [
        {"match": "India vs Australia", "date": "2024-07-01"},
        {"match": "England vs New Zealand", "date": "2024-07-02"},
        {"match": "Pakistan vs South Africa", "date": "2024-07-03"},
    ]

@tool("get_team_rankings", description="Fetches the current team rankings.")
def get_team_rankings():
    """ Fetches the current team rankings. """
    return [
        {"team": "India", "rank": 1},
        {"team": "Australia", "rank": 2},
        {"team": "England", "rank": 3},
        {"team": "New Zealand", "rank": 4},
        {"team": "Pakistan", "rank": 5},
        {"team": "South Africa", "rank": 6},
    ]

@tool
def get_player_stats(player_name):
    """ Fetches the stats for a given player. """
    stats = {
        "Virat Kohli": {"matches": 254, "runs": 12040, "average": 59.33},
        "Steve Smith": {"matches": 128, "runs": 7540, "average": 61.80},
        "Joe Root": {"matches": 150, "runs": 8300, "average": 52.45},
    }
    return stats.get(player_name, "Player not found")

@tool
def update_preferred_team(team_name: str, runtime: ToolRuntime) -> Command:
    """ Updates the user's preferred team. """
    print(f"Updating preferred team to: {team_name}")
    return Command(update={"preferred_team": team_name,
                           "messages": [ToolMessage(content=f"Preferred team updated to {team_name}", tool_call_id=runtime.tool_call_id)]})

@tool
def get_preferred_team(runtime: ToolRuntime) -> str:
    """ Retrieves the user's preferred team. """
    print("Retrieving preferred team")
    print(f"Current state: {runtime.state}")
    return runtime.state.get("preferred_team", "No preferred team set")

@dataclass
class UserContext:
    user_name: str