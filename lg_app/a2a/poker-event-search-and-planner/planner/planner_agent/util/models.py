from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

class ChatModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    role: str
    content: str
    # validation_alias - used to name the field in the json input
    # serialization_alias - used to name the field in the json output
    thread_id: str = Field(alias="threadId")
    email: str
    timestampInUtcMillis: int | None = None

class ConversationHistory(BaseModel):
    pass


"""
sample A2A Request:

{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "request_1234",
    "params": {
        "message": {
            "role": "user",
            "contextId": "conversation_5678",
            "taskId": "task_91011",
            "messageId": "0f8b9c2e-4d3a-4e5b-9c1a-2f3e4d5f6a7b",
            "parts": [
                {
                    "kind": "text",
                    "text": "What is the weather like today?"
                }
            ]
        }
    }
}


sample A2A Response:

{
    "jsonrpc": "2.0",
    "id": "request_1234",
    "result": {
        "contextId": "conversation_5678",
        "artifacts": [
            {
                "parts": [
                    {
                        "kind": "text",
                        "text": "What is the weather like today?"
                    }
                ]
            }
        ],
        "status": "success"
    }
}

"""

class A2AMessage(BaseModel):
    role: str = Field(..., description="The role of the message sender, e.g., 'user', 'assistant', or 'system'.")
    contextId: Optional[str] = Field(None, description="Optional conversation tracking identifier to maintain multi-turn context between agents.")
    taskId: Optional[str] = Field(None, description="Optional task tracking identifier to maintain multi-turn context for a specific task.")
    parts: list[Dict[str, Any]] = Field(..., description="A list of message parts, each containing a 'kind' and 'text'.")
    messageId: str = Field(default_factory=lambda: str(uuid.uuid4()), description="A unique identifier for the message.")

class A2ARequestParams(BaseModel):
    """
    A2ARequestParams is a Pydantic model that represents the parameters for the A2A API request.
    """
    # skill: str = Field(..., description="The name of the skill to be invoked by the agent.")
    # arguments: Dict[str, Any] = Field(..., description="A dictionary containing the arguments for the skill being invoked.")
    # contextId: Optional[str] = Field(None, description="Optional conversation tracking identifier to maintain multi-turn context between agents.")
    message: A2AMessage = Field(..., description="The message to be sent in the request.")

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

class A2AResponseArtifcat(BaseModel):
    """
    A2AResponseArtifact is a Pydantic model that represents an artifact in the A2A API response.
    """
    parts: list[Dict[str, Any]] = Field(..., description="A list of message parts, each containing a 'kind' and 'text'.")

class A2AResponseResult(BaseModel):
    """
    A2AResponseResult is a Pydantic model that represents the result field in the A2A API response.
    """
    artifacts: list[A2AResponseArtifcat] = Field(..., description="A list of artifacts returned by the agent in response to the request.")
    contextId: Optional[str] = Field(None, description="Optional conversation tracking identifier to maintain multi-turn context between agents.")
    status: str = Field(..., description="The status of the API call, e.g., 'success', 'error', etc.")

class A2AResponse(BaseModel):
    """
    A2AResponse is a Pydantic model that represents the response body for the A2A API.
    """
    jsonrpc: str = Field("2.0", description="The JSON-RPC version, which is always '2.0'.")
    id: str = Field(..., description="A unique identifier for the request, which is used to match responses with requests.")
    result: A2AResponseResult = Field(..., description="The result of the API call.")
    
    
if __name__ == "__main__":
    # Example usage
    request = A2ARequest(
        jsonrpc="2.0",
        method="message/send",
        id="request_1234",
        params=A2ARequestParams(
            message=A2AMessage(
                role="user",
                contextId="conversation_5678",
                taskId="task_91011",
                messageId="0f8b9c2e-4d3a-4e5b-9c1a-2f3e4d5f6a7b",
                parts=[{"kind": "text", "text": "What is the weather like today?"}]
            )
        )
    )

    print(request.model_dump())
    
    response = A2AResponse(
        jsonrpc="2.0",
        id="request_1234",
        result=A2AResponseResult(
            contextId="request_1234",
            artifacts=[
                {
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Hello world"
                        }
                    ]
                }
            ],
            status="success"
        )
    )
    
    print(response.model_dump())