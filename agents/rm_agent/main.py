from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
import datetime
from utils.models import ChatRequest
from utils.resource_registry import ResourceRegistry
import os
from utils.env_settings import EnvSettings
from utils.rm_agent import RecipeManagerAgent
from utils.database import save_messages, get_messages_by_thread_id_from_redis

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

        # setup database engine
        resource_registry.create_database_engine(settings.database_url)

        # setup redis client
        resource_registry.setup_redis_client(
            host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)

        app.state.resources = resource_registry
        print("server startup completed...")

        yield
        print("server shutdown initiated...")
        await resource_registry.dispose_database_engine()
        print("server shutdown completed...")

    except Exception as e:
        print(f"error setting up resource registry : {e}")
    finally:
        await resource_registry.cleanup()


app = FastAPI(title="RM AI Agent Server", lifespan=lifespan)


@app.get("/health")
def health():
    print("Server is healthy")
    return f"server is healthy current time is {datetime.datetime.now()}"


@app.post("/chat/{thread_id}")
async def chat(thread_id: str, data: ChatRequest, request: Request, background_tasks: BackgroundTasks):
    print(f"chat function called with {data}")

    # load messages for the current conversation thread

    # always send the request to the main agent
    resource_registry: ResourceRegistry = request.app.state.resources
    client: RecipeManagerAgent = resource_registry.ai_clients["main_agent"]
    history = get_messages_by_thread_id_from_redis(resource_registry.redis_client, thread_id) or []
    
    # print(f"history {history}")
    
    new_messages = await client.orchestrate(data, history=history, mcp_session_map=resource_registry.mcp_sessions,
                                        toolname_servername_map=resource_registry.toolname_servername_map)
    print(new_messages)
    if not new_messages:
        return {"error": "failed to get response from agent"}

    # summarize the messages
    # persist messages to the long term and short term memory stores (database and redis)
    _persist_messages(resource_registry.async_session, resource_registry.redis_client, thread_id,
                      background_tasks, new_messages)

    return {"message": new_messages[-1]["content"]}


def _persist_messages(async_sessionmaker, r, thread_id: str, background_tasks: BackgroundTasks, messages: list):
    """ persist messages to database """
    background_tasks.add_task(
        save_messages, async_sessionmaker, r, thread_id, messages)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
