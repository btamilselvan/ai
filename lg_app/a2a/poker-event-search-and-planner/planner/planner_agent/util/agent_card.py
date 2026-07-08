from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated, Literal
from pydantic.alias_generators import to_camel
import json

class Provider(BaseModel):
    name: str
    url: str
    contact: Optional[str] = None

class InputSchema(BaseModel):
    type: str
    properties: dict
    required: list
    

class AuthSchema(BaseModel):
    schemes: list[str] = Field(... , description="List of authentication schema names this agent supports")
    description: str

class AgentSkill(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)
    
    name: str = Field(..., description="Unique name of the skill within the agent")
    id: str = Field(..., description="Unique identifier for the skill")
    description: str
    input_schema: InputSchema = Field(alias="inputSchema")

class AgentCapabilities(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)
    
    streaming: bool = Field(default=False, description="Whether the agent supports streaming responses")
    push_notification: bool = Field(default=False, description="Whether the agent supports push notifications", alias="pushNotification")
    a2a_version: str = Field(alias="a2aVersion", default="1.0.0", description="A2A protocol version supported by the agent")


class AgentCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)
    
    name: str
    description: str
    version: str
    provider: Optional[dict] = None
    
    # where the agent is hosted
    url: str
    capabilities: AgentCapabilities = Field(alias="capabilities")
    skills: list[AgentSkill]
    
    # keywords for searching and discovery
    tags: Optional[list[str]] = None
    
    authentication: Optional[AuthSchema] = None
    
    last_updated: str = Field(alias="lastUpdated")
    
class SearchEventArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)
    
    min_datetime: dict = Field(..., alias="minDatetime", description="The start datetime for the events. MUST be striclty in 'YYYY-MM-DD HH:MM:SS' format.")
    max_datetime: dict = Field(..., alias="maxDatetime", description="The end datetime for the events. MUST be striclty in 'YYYY-MM-DD HH:MM:SS' format.")
    
def build_agent_card():
    
    agent_card = AgentCard(
        name="Event Search and Planning Agent",
        description="An agent that helps users search for events and plan their attendance",
        version="1.0.0",
        provider={
            "name": "Poker Event Planner Inc",
            "url": "https://planner.tamils.rokcs",
            "contact": "support@tamils.rocks"
        },
        url="https://planner.tamils.rokcs",
        capabilities=AgentCapabilities(streaming=False, push_notification=False, a2a_version="1.0.0"),
        skills=[
            AgentSkill(
                name="Search Events",
                id="search_events",
                description="Search for available events based on date range",
                input_schema=InputSchema(
                    type="object",
                    properties={
                        "minDatetime": {"type": "string", "format": "date-time", "description": "The starting ISO 8601 date-time filter (e.g., 2026-06-01T00:00:00Z)"},
                        "maxDatetime": {"type": "string", "format": "date-time", "description": "The ending ISO 8601 date-time filter (e.g., 2026-07-01T00:00:00Z)"},
                    },
                    required=["minDatetime", "maxDatetime"]
                )
            )
        ],
        tags=["events", "planning"],
        authentication=AuthSchema(
            schemes=["api_key"],
            description="Supports API key authentication"
        ),
        last_updated="2026-06-01"
    )
    
    print(json.dumps(agent_card.model_dump(), indent=2))


if __name__ == "__main__":
    build_agent_card()
