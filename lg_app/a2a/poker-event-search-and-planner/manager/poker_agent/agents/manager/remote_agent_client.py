from poker_agent.agents.manager.models import A2ARequestParams, A2ARequest, A2AResponse
import random
import os
from poker_agent.utils.app_state import AppState
import logging
import requests

logger = logging.getLogger(__name__)

def _createA2ARequest(task_description, app_state: AppState):
    return A2ARequest(
        jsonrpc="2.0",
        method="message/send",
        id=f"{random.randint(1000, 9999)}",
        params=A2ARequestParams(
            message={
                "role": "user",
                "contextId": app_state.thread_id,
                "taskId": f"task_{random.randint(1000, 9999)}",
                "parts": [
                    {
                        "kind": "text",
                        "text": task_description
                    }
                ],
                "messageId": f"msg_{random.randint(1000, 9999)}"
            }
        )
    )


def delegate_to_planner_tool(task_description, app_state: AppState):
    headers = {"Content-Type": "application/json", "x-api-key": os.getenv("A2A_API_KEY"), "x-user-email": app_state.email}
    
    user_email = app_state.email or "tamil@tamils.rocks"
    
    logger.info("Delegating to planner with task description: %s and user email: %s", task_description, user_email)
    
    request_payload = _createA2ARequest(task_description, app_state)
    
    logger.info("Sending request to planner agent: %s", request_payload)
    
    response = requests.post(os.getenv("PLANNER_AGENT_URL"), json=request_payload.model_dump(), headers=headers)
    
    logger.info("Received response from planner agent: %s", response.json())
    
    a2a_response = A2AResponse.model_validate(response.json())
    
    logger.info("Returning response from planner agent: %s", a2a_response)
    
    return a2a_response.result.artifacts and a2a_response.result.artifacts[0].parts and a2a_response.result.artifacts[0].parts[0].get("text", "Unable to retrieve response") or "No artifacts found"