from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import uvicorn
import datetime
from utils.models import ChatRequest, AppState, ConversationModel
from utils.resource_registry import ResourceRegistry
import os
from utils.env_settings import EnvSettings
from agents.supervisor import SupervisorAgent
from datastore.database import load_appstate_from_redis
from redis import Redis
import logging
from utils.background_task import run_background_tasks
import traceback

load_dotenv()

settings = EnvSettings()


logging.basicConfig(
    level=logging.INFO,
    # include thread id
    format="%(asctime)s [%(levelname)s] [%(filename)s %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[
        logging.StreamHandler()  # log to console
    ]
)
logger = logging.getLogger(__name__)


async def lifespan(app: FastAPI):
    """ initialize singleton resources (mcp clients, ai clients, etc.) """

    # print("server startup initiated...")
    logger.info("server startup initiated...")

    # print(f"mcp servers : {settings.mcp_servers}")
    logger.info("mcp servers %s", settings.mcp_servers)

    resource_registry = ResourceRegistry()

    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

    try:
        logger.info("trying to connect to mcp server(s)...")

        # setup mcp clients and load tools
        for name, url in settings.mcp_servers.items():
            logger.info("connecting to mcp server %s at %s...", name, url)
            await resource_registry.setup_mcp_client(name, url, settings.mcp_server_api_key)

        # setup openai client
        resource_registry.setup_openai_client(
            url="https://api.deepseek.com", api_key=DEEPSEEK_API_KEY)

        all_tools = []
        # make all tools available to the main agent (for now)
        for mcp_server_name, tools in resource_registry.tools_map.items():
            all_tools.extend(tools)

        # setup ai clients
        for name, model in settings.agents.items():
            logger.debug(
                "setting up ai agent %s with model %s...", name, model)
            resource_registry.setup_ai_client(
                name, resource_registry.openai_client, model, tools=all_tools)

        # setup database engine
        resource_registry.create_database_engine(settings.database_url)

        # setup redis client
        resource_registry.setup_redis_client(
            host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)

        app.state.resources = resource_registry
        logger.info("server startup completed...")

        yield
        logger.info("server shutdown initiated...")
        await resource_registry.dispose_database_engine()
        logger.info("server shutdown completed...")

    except Exception as e:
        logger.error(f"error setting up resource registry : {e}")
        traceback.print_exc()
        raise
    finally:
        await resource_registry.cleanup()


app = FastAPI(title="RM AI Agent Server", lifespan=lifespan)


@app.get("/health")
def health():
    logger.info("Server is healthy")
    return f"server is healthy current time is {datetime.datetime.now()}"


@app.post("/chat/{thread_id}", responses={
    429: {"description": "Another request is being processed for this thread"},
    500: {"description": "Error processing the request"}
})
async def chat(thread_id: str, data: ChatRequest, request: Request, background_tasks: BackgroundTasks):
    logger.info("chat function called with thread id: %s", thread_id)

    resource_registry: ResourceRegistry = request.app.state.resources

    # lock the thread
    lock_key = f"thread_lock:{thread_id}"
    r: Redis = resource_registry.redis_client
    # try to acquire lock, if lock is acquired proceed with processing the request, else return an error response indicating that another request is being processed for this thread
    if r.set(lock_key, "processing", ex=60, nx=True):

        try:
            logger.info("acquired lock for thread %s", thread_id)
            # always send the request to the main agent
            client: SupervisorAgent = resource_registry.ai_clients["supervisor_agent"]

            original_state = __load_appstate(thread_id, r, data)
            working_state = original_state.model_copy(deep=True)

            working_state = await client.orchestrate(working_state,
                                                         mcp_client_map=resource_registry.mcp_clients)

            messages_count = len(working_state.messages)
            working_state.messages_count = messages_count

            logger.debug(f"updated appstate {working_state}")

            logger.debug("old messages count %d, new messages count %d",
                         original_state.messages_count, working_state.messages_count)

            if messages_count <= original_state.messages_count:
                return {"error": "failed to get response from agent"}

            # summarize the messages
            # persist messages to the long term and short term memory stores (database and redis)
            background_tasks.add_task(
                run_background_tasks, resource_registry, working_state)

            return {"message": working_state.messages[-1].content}
        except Exception as e:
            logger.error("error in chat endpoint: %s", e)
            traceback.print_exc()
            raise HTTPException(
                status_code=500, detail=f"error processing the request: {e}")
        finally:
            r.delete(lock_key)
            logger.info("released lock for thread %s", thread_id)
    else:
        logger.warning(
            f"failed to acquire lock for thread {thread_id}, another request is being processed for this thread")
        raise HTTPException(
            status_code=429, detail="another request is being processed for this thread, please try again later")


def __load_appstate(thread_id: str, r: Redis, data: ChatRequest) -> AppState:

    app_state = load_appstate_from_redis(r, thread_id)

    history = app_state.messages or []
    messages_count = len(history)

    logger.debug("length of history: %s", messages_count)

    user_message = ConversationModel(thread_id=thread_id,
                                     role="user", content=data.message)

    app_state.messages_count = messages_count
    app_state.user_message = data.message

    messages = history + [user_message]
    app_state.messages = messages
    app_state.current_agent_name = "supervisor_agent"

    logger.debug(f"history {messages}")
    return app_state


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
