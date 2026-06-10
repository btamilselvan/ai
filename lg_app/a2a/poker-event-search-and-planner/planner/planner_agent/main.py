import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[logging.StreamHandler()],
)

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
from fastapi import HTTPException, Request
from planner_agent.util.google_resources import (
    save_token,
    get_calendar_info,
    get_refresh_token as get_refresh_token_from_db,
)
import redis

logger = logging.getLogger(__name__)
logger.info("Planner Agent is starting up...")

load_dotenv()

# API Key Header name
API_KEY_HEADER_NAME = "x-api-key"

# How to read API Key Header
header_scheme = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=True)


async def build_graph():
    graph = StateGraph(AppState)

    graph.add_node("llm_node", llm_node)
    graph.add_node("tools", tool_node_wrapper)

    graph.add_edge(START, "llm_node")
    graph.add_conditional_edges("llm_node", tools_condition)
    graph.add_edge("tools", "llm_node")

    app = graph.compile()
    logger.info(app.get_graph().draw_ascii())

    return app


async def lifespan(app: FastAPI):
    """initialize langgraph app"""
    logger.info("server is starting up..")
    await build_graph()

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
    logger.info("current date time is %s", str(datetime.datetime.now()))
    return {"status": "healthy", "datetime": str(datetime.datetime.now())}


@app.post("/google/credentials")
def save_google_credentials(
    credentials: dict, redis: redis.Redis = Depends(get_redis_client)
):
    email = credentials.get("email")
    logger.info("save google token %s for user %s", credentials, email)
    save_token(email, credentials, redis)
    return {"status": "success"}


@app.get("/google/token/refresh")
def get_refresh_token(email, redis: Redis = Depends(get_redis_client)):
    logger.info("get refresh token for %s", email)
    token = get_refresh_token_from_db(email, redis)
    if token:
        return {"refresh_token": token}
    else:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh token does not exist",
        )


@app.get("/google/calendar/info")
def chat(email, redis: redis.Redis = Depends(get_redis_client)):
    logger.info("get calendar info for user %s", email)
    get_calendar_info(email, redis)
    return {"status": "success"}
