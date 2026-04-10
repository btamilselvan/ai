from dotenv import load_dotenv
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
import uvicorn
import datetime
from utils.models import ChatRequest
from utils.resource_registry import ResourceRegistry
import os
from utils.env_settings import EnvSettings
from utils.rm_agent import RecipeManagerAgent
from utils.database import get_messages_by_thread_id_from_redis
from redis import Redis
import logging
from utils.background_task import run_background_tasks

load_dotenv()

settings = EnvSettings()


logging.basicConfig(
        level=logging.INFO,
        #include thread id
        format="%(asctime)s [%(levelname)s] [Thread-%(thread)d] %(message)s",
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
            logger.debug("setting up ai agent %s with model %s...", name, model)
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
            client: RecipeManagerAgent = resource_registry.ai_clients["main_agent"]

            # load messages for the current conversation thread
            history = get_messages_by_thread_id_from_redis(
                resource_registry.redis_client, thread_id) or []

            # logger.debug(f"history {history}")

            new_messages = await client.orchestrate(data, history=history, mcp_session_map=resource_registry.mcp_sessions,
                                                    toolname_servername_map=resource_registry.toolname_servername_map)
            # logger.debug(f"new messages {new_messages}")
            if not new_messages:
                return {"error": "failed to get response from agent"}

            # summarize the messages
            # persist messages to the long term and short term memory stores (database and redis)
            # _persist_messages(resource_registry.async_session, resource_registry.redis_client, thread_id,
            #                   background_tasks, new_messages)
            background_tasks.add_task(run_background_tasks, resource_registry, thread_id, new_messages)

            return {"message": new_messages[-1]["content"]}
        except Exception as e:
            logger.error("error in chat endpoint: %s", e)
            raise HTTPException(status_code=500, detail=f"error processing the request: {e}")
        finally:
            r.delete(lock_key)
            logger.info("released lock for thread %s", thread_id)
    else:
        logger.warning(
            f"failed to acquire lock for thread {thread_id}, another request is being processed for this thread")
        raise HTTPException(status_code=429, detail="another request is being processed for this thread, please try again later")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
