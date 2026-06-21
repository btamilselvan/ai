import os
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[logging.StreamHandler()],
)

from functools import partial
from langgraph.graph import StateGraph, START, END
from planner_agent.util.app_state import AppState
from planner_agent.agent.nodes import llm_node, tool_node_wrapper
from langchain.messages import HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from fastapi import FastAPI, Depends, Security, status, HTTPException
import datetime
from planner_agent.util.resource_registry import ResourceRegistry
from dotenv import load_dotenv
from fastapi.security import APIKeyHeader
from typing import Annotated
from fastapi import HTTPException, Request, Response
from planner_agent.util.google_resources import (
    save_token,
    update_access_token as update_google_access_token,
    get_calendar_info as google_calendar_info,
    get_refresh_token as get_refresh_token_from_db,
    get_current_datetime as google_calendar_datetime,
    search_events as google_search_events,
)
import redis
from planner_agent.util.redis_db import get_appstate, save_appstate
from planner_agent.util.models import ChatModel

logger = logging.getLogger(__name__)
logger.info("Planner Agent is starting up...")

load_dotenv()

# API Key Header name
API_KEY_HEADER_NAME = "x-api-key"

# How to read API Key Header
header_scheme = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)


async def build_graph(redis_client: redis.Redis):
    graph = StateGraph(AppState)

    graph.add_node("llm_node", llm_node)
    graph.add_node("tools", partial(tool_node_wrapper, r=redis_client))

    graph.add_edge(START, "llm_node")
    graph.add_conditional_edges("llm_node", tools_condition)
    graph.add_edge("tools", "llm_node")
    global app
    app = graph.compile()
    logger.info(app.get_graph().draw_ascii())

    return app


async def lifespan(app: FastAPI):
    """initialize langgraph app"""
    logger.info("server is starting up..")

    # configure redis client
    pool = redis.ConnectionPool(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        db=os.getenv("REDIS_DB"),
        max_connections=10,
    )
    redis_client = redis.Redis(connection_pool=pool)
    logger.info("redis client configured successfully %s", redis_client.info)
    app.state.redis_client = redis_client

    await build_graph(redis_client)

    yield
    logger.info("server shutdown initiated..")


def validate_api_key(api_key: str = Security(header_scheme)):
    logger.info("validating api key %s", api_key)
    if not api_key or api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )

    return api_key


def get_redis_client(request: Request):
    return request.app.state.redis_client


app = FastAPI(
    lifespan=lifespan,
    description="Planner AI Agent with Google Calendar access",
    dependencies=[Depends(validate_api_key)],
)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    logger.info("current date time is %s", str(datetime.datetime.now()))
    return {"status": "healthy", "datetime": str(datetime.datetime.now())}


@app.post(
    "/google/credentials",
    summary="Save google credentials (accessToken, refreshToken, email) in the database.",
)
def save_google_credentials(
    credentials: dict, redis: redis.Redis = Depends(get_redis_client)
):
    """Save google credentials (accessToken, refreshToken, email) in the database."""
    email = credentials.get("email")
    logger.info("save google token %s for user %s", credentials, email)
    save_token(email, credentials, redis)
    return {"status": "success"}


@app.get("/google/token/refresh", summary="Get refresh token for the user")
def get_refresh_token(email, redis: Redis = Depends(get_redis_client)):
    """Get refresh token for the user"""
    logger.info("get refresh token for %s", email)
    token = get_refresh_token_from_db(email, redis)
    if token:
        return {"refresh_token": token}
    else:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh token does not exist",
        )

@app.put("/google/token", summary="Update Access token for the user")
def update_access_token(data: dict, redis: redis.Redis = Depends(get_redis_client)):
    """ update access token for the user """
    logger.info("update access token for user %s", data)
    update_google_access_token(data.get("email"), data.get("accessToken"), redis)
    return {"status": "success"}

@app.get("/google/calendar/info")
def get_calendar_info(email, redis: redis.Redis = Depends(get_redis_client)):
    logger.info("get calendar info for user %s", email)
    data = google_calendar_info(email, redis)

    return {
        "status": "success", "data": json.loads(data)
    }


@app.get("/google/calendar/datetime")
def get_calendar_datetime(email, redis: redis.Redis = Depends(get_redis_client)):
    logger.info("get google_calendar_datetime info for user %s", email)
    google_calendar_datetime(email, redis)
    return {"status": "success"}

@app.get("/google/calendar/search", summary="Search events in the user's calendar")
def search_events(email, min, max, r: redis.Redis = Depends(get_redis_client)):
    response = google_search_events(email, r, min, max, True, None)
    return {"events": response}


@app.post("/chat", summary="Chat with Calendar/Planner agent")
def chat(
    body: ChatModel,
    redis: redis.Redis = Depends(get_redis_client),
):
    logger.info("request received %s", body)
    # retrieve app state for the email and thread id
    current_state: AppState = get_appstate(body.email, body.thread_id, redis)
    # logger.info("retrieved app state %s", current_state)
    history = current_state.messages or []
    # add current user message to the history
    messages = history + [HumanMessage(content=body.message)]

    # update app state
    # invoke LLM
    new_state = app.invoke(
        AppState(messages=messages, thread_id=body.thread_id, email=body.email)
    )
    # logger.info("response from llm %s, type %s", new_state, type(new_state))

    # persist app state back to redis
    save_appstate(new_state, redis)

    logger.info("final response %s", new_state["messages"][-1].content)

    return {
        "response": new_state["messages"][-1].content,
        "thread_id": body.thread_id,
        "email": body.email,
    }
