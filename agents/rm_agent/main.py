from dotenv import load_dotenv
from fastapi import FastAPI, Request
import uvicorn
import datetime
from utils.models import ChatRequest
from utils.resource_registry import ResourceRegistry
import os
from utils.env_settings import EnvSettings
from utils.rm_agent import RecipeManagerAgent

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

settings = EnvSettings()


async def lifespan(app: FastAPI):
    """ initialize singleton resources (mcp clients, ai clients, etc.) """

    print("server startup initiated...")

    print(f"mcp servers : {settings.mcp_servers}")

    resource_registry = ResourceRegistry()

    try:
        print("trying to connect to mcp server(s)...")

        # setup mcp clients and load tools
        for name, url in settings.mcp_servers.items():
            print(f"connecting to mcp server {name} at {url}...")
            await resource_registry.setup_mcp_client(name, url)

        # setup openai client
        resource_registry.setup_openai_client(
            url="https://api.deepseek.com", api_key=DEEPSEEK_API_KEY)

        all_tools = []
        # make all tools available to the main agent (for now)
        for mcp_server_name, tools in resource_registry.tools_map.items():
            all_tools.extend(tools)

        # setup ai clients
        for name, model in settings.agents.items():
            print(f"setting up ai agent {name} with model {model}...")
            resource_registry.setup_ai_client(
                name, resource_registry.openai_client, model, tools=all_tools)

        app.state.resources = resource_registry
        print("server startup completed...")

        yield
        print("server shutdown initiated...")

    except Exception as e:
        print(f"error setting up resource registry : {e}")
    finally:
        await resource_registry.cleanup()


app = FastAPI(title="RM AI Agent Server", lifespan=lifespan)


@app.get("/health")
def health():
    print("Server is healthy")
    return f"server is healthy current time is {datetime.datetime.now()}"


@app.post("/chat")
async def chat(data: ChatRequest, request: Request):
    print(f"chat function called with {data}")

    # always send the request to the main agent
    resource_registry: ResourceRegistry = request.app.state.resources
    client: RecipeManagerAgent = resource_registry.ai_clients["main_agent"]
    response = await client.orchestrate(data, mcp_session_map=resource_registry.mcp_sessions,
                                        toolname_servername_map=resource_registry.toolname_servername_map)
    print(response)
    if not response:
        return {"error": "failed to get response from agent"}
    return {"message": response.choices[0].message.content}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
