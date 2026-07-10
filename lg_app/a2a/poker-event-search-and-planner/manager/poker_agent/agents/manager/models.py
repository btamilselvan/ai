from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class A2ARequestParams(BaseModel):
    """
    A2ARequestParams is a Pydantic model that represents the parameters for the A2A API request.
    """
    skill: str = Field(..., description="The name of the skill to be invoked by the agent.")
    arguments: Dict[str, Any] = Field(..., description="A dictionary containing the arguments for the skill being invoked.")
    contextId: Optional[str] = Field(None, description="Optional conversation tracking identifier to maintain multi-turn context between agents.")

class A2ARequest(BaseModel):
    """
    A2ARequest is a Pydantic model that represents the request body for the A2A API.
    It complies with JSON-RPC 2.0 framework transports.
    """
    # Using Literal ensures Pydantic rejects any request that isn't exactly "2.0"
    jsonrpc: str = Field("2.0", description="The JSON-RPC version, which is always '2.0'.")
    
    method: str = Field(..., description="The transport method. Usually 'message/send' for execution, or 'message/stream' for tokens.")
    
    id: str = Field(..., description="A unique identifier for the request, which is used to match responses with requests.")
    params: A2ARequestParams = Field(..., description="The parameters for the method being invoked.")

class A2AResponseResult(BaseModel):
    """
    A2AResponseResult is a Pydantic model that represents the result field in the A2A API response.
    It contains a single field, 'response', which is a string representing the response to the user's query.
    """
    output: dict = Field(..., description="The response to the user's query, which is a dictionary.")
    contextId: Optional[str] = Field(None, description="Optional conversation tracking identifier to maintain multi-turn context between agents.")

class A2AResponse(BaseModel):
    """
    A2AResponse is a Pydantic model that represents the response body for the A2A API.
    It contains a single field, 'response', which is a string representing the response to the user's query.
    """
    jsonrpc: str = Field("2.0", description="The JSON-RPC version, which is always '2.0'.")
    id: str = Field(..., description="A unique identifier for the request, which is used to match responses with requests.")
    result: A2AResponseResult = Field(..., description="The result of the API call.")