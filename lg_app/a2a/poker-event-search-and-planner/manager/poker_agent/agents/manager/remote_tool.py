import requests
from langchain_core.tools import StructuredTool
import logging
from poker_agent.agents.manager.models import A2ARequestParams, A2ARequest, A2AResponse
import random
import os

# logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def excute_remote_tool_function(skill_id: str, a2a_endpoint):
    
    ### When an inner function is created inside an outer function, it remembers the environment it was born in. 
    # Specifically, it hooks onto any variables in the outer function's scope—in this case, skill_id.
    ## Even after make_execution_function finishes executing and exits, the inner _execute_remote_tool function holds onto that specific skill_id variable forever. 
    # This packaged bundle of a function paired with its surrounding environment is called a closure.
    def _execute_remote_tool(**kwargs):
            """ internal function to execute the remote tool with the provided arguments """
            logger.info("Executing remote tool with args: %s skill: %s, a2a_endpoint: %s", kwargs, skill_id, a2a_endpoint)
            
            headers = {"Content-Type": "application/json", "x-api-key": os.getenv("A2A_API_KEY")}
            
            ## add email id to kwargs
            updated_kwargs = {**kwargs, "email": "tamil.ts@gmail.com"}

            # A2A standard payload format
            payload = A2ARequest(
                jsonrpc="2.0",
                method="message/send",
                id=f"request_{random.randint(1000, 9999)}",
                params=A2ARequestParams(
                    skill=skill_id,
                    arguments=updated_kwargs,
                )
            )

            response = requests.post(a2a_endpoint, json=payload.model_dump(), headers=headers)
            a2a_response = A2AResponse.model_validate(response.json())
            # logger.info("A2A response: %s", a2a_response)
            tool_output = a2a_response.result.output if isinstance(a2a_response.result.output, dict) else {"data": a2a_response.result.output}
            # logger.info("Tool output: %s", tool_output)
            data = tool_output.get("data", "no calendar events found")
            logger.info("Final data to return: %s", data)
            return data
    return _execute_remote_tool
    

def register_remote_agent(agent_name: str, agent_url: str):
    """
    Registers a remote agent with the given name and URL.

    Args:
        agent_name (str): The name of the agent to register.
        agent_url (str): The URL of the remote agent.

    Raises:
        ValueError: If the agent name or URL is invalid.
    """
    if not agent_name or not isinstance(agent_name, str):
        raise ValueError("Agent name must be a non-empty string.")
    if not agent_url or not isinstance(agent_url, str):
        raise ValueError("Agent URL must be a non-empty string.")
    
    # Fetch agent-card.json from the remote agent
    try:
        response = requests.get(f"{agent_url}/.well-known/agent-card.json")
        response.raise_for_status()
        agent_card = response.json()
        logger.info("Fetched agent card for %s: %s", agent_name, agent_card)
        
        logger.info("agent description: %s", agent_card.get("description", "No description provided"))
        logger.info("agent skills: %s", agent_card.get("skills", []))
     
        # Convert the list of skills into a list of StructuredTool objects
        tools = []
        for skill in agent_card.get("skills", []):
            logger.info("Registering skill: %s", skill.get("name"))
            bound_func = excute_remote_tool_function(skill.get("id"), a2a_endpoint=agent_card.get("a2aEndpoint"))
            tool = StructuredTool.from_function(
                func=bound_func,
                name=skill.get("id"),
                description=skill.get("description", ""),
                args_schema=skill.get("inputSchema", {}),
            )
            tools.append(tool)
        
        return tools
        
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch agent card from {agent_url}: {e}")
    
def fetch_agent_skills(agent_url: str):
    """
    Fetches the skills of a remote agent from its agent-card.json.

    Args:
        agent_url (str): The URL of the remote agent.
    Returns:
        list: A list of skills (dictionaries) of the remote agent.
    Raises:
        ValueError: If the agent URL is invalid or if fetching the skills fails.
    """
    if not agent_url or not isinstance(agent_url, str):
        raise ValueError("Agent URL must be a non-empty string.")

    try:
        response = requests.get(f"{agent_url}/.well-known/agent-card.json")
        response.raise_for_status()
        agent_card = response.json()
        skills = agent_card.get("skills", [])
        
        return "\n".join([f"Skill: {skill.get('name')} | Description: {skill.get('description')}\n" for skill in skills])

    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch agent skills from {agent_url}: {e}")

    
if __name__ == "__main__":
    # Example usage
    try:
        # register_remote_agent("Event Search and Planning Agent", "http://localhost:9000")
        print(fetch_agent_skills("http://localhost:9000"))
    except ValueError as e:
        logger.exception("Error registering remote agent: %s", e)