from pydantic import BaseModel, Field
from typing import Literal, Union


class MatchInfo(BaseModel):
    """ Schema for a single cricket match."""
    series_name: str = Field(description="Name of the cricket series")
    match_desc: str = Field(description="Description of the match")
    match_format: str = Field(
        description="Format of the match (e.g., Test, ODI, T20)")
    start_date: str = Field(
        description="Start date of the match in epoch time")
    end_date: str = Field(description="End date of the match in epoch time")
    team1: str = Field(description="Name of the first team")
    team2: str = Field(description="Name of the second team")
    venue: str = Field(description="Venue of the match")


class CricketMatchesResponse(BaseModel):
    """ Schema for the response from the get_upcoming_cricket_matches tool."""
    type: Literal["match_list"] = "match_list"
    matches: list[MatchInfo] = Field(
        description="List of upcoming cricket matches")
    has_matches: bool = Field(
        description="Indicates if there are upcoming matches")
    agent_summary: str = Field(description="A brief summary of the response to provide context to the user")


class GeneralChatResponse(BaseModel):
    """ Schema for general agent responses that are not tool responses."""
    type: Literal["chat"] = "chat"
    content: str = Field(description="The content of the agent's response")


class AgentErrorResponse(BaseModel):
    """ Schema for error responses from the agent."""
    type: Literal["error"] = "error"
    error_message: str = Field(
        description="Error message describing what went wrong")


class CricketToolResponseFormat(BaseModel):
    """ Unified response format for the cricket agent, encompassing both tool responses and general chat responses."""
    structured_response: Union[CricketMatchesResponse, GeneralChatResponse, AgentErrorResponse] = Field(
        discriminator="type", description="The structured response from the agent, which can be a tool response, a general chat response, or an error response")
