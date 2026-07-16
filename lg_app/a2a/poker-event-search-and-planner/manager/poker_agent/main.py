import os
import logging
import json
import random
import string
from datetime import datetime as datetime_cls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[logging.StreamHandler()],
)

from functools import partial
from langgraph.graph import StateGraph, START, END
from langchain.messages import HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from fastapi import FastAPI, Depends, Security, status, HTTPException
import datetime

from dotenv import load_dotenv
from fastapi.security import APIKeyHeader
from typing import Annotated
from fastapi import HTTPException, Request, Response
from poker_agent.agents.manager.nodes import llm_node, tool_node_wrapper, conditional_node, planner_node, custom_tool_node
from poker_agent.utils.app_state import AppState
from poker_agent.utils.redis_db import get_appstate, save_appstate
from poker_agent.utils.models import ChatModel


import redis

logger = logging.getLogger(__name__)
logger.info("Planner Agent is starting up...")

load_dotenv()

# API Key Header name
API_KEY_HEADER_NAME = "x-api-key"

# How to read API Key Header
header_scheme = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)

PUBLIC_ROUTES = ["/health", "/.well-known/agent-card.json"]


async def build_graph(redis_client: redis.Redis):
    graph = StateGraph(AppState)
    
    graph.add_node("manager_node", llm_node)

    # tools_condition would result "tools" or "END" so tool_name should be "tools"
    # graph.add_node("tools", tool_node_wrapper)
    graph.add_node("tools", custom_tool_node)

    # planner node
    graph.add_node("planner", planner_node)

    graph.add_edge(START, "manager_node")
    # https://reference.langchain.com/python/langgraph.prebuilt/tool_node/tools_condition
    # tools_condition checks the last message from the LLM node for any tool calls. If there are tool calls, it goes to the "tools" node, otherwise it goes to END.
    # app.add_conditional_edges("manager_node", tools_condition)

    graph.add_conditional_edges("manager_node", conditional_node, {
        "tools": "tools",
        "planner": "planner",
        "END": END
    })

    # tools node will execute the tool calls and then go back to the manager_node to get the next response from the LLM based on the tool results. This loop continues until there are no more tool calls required and the planner_node directs it to END.
    graph.add_edge("tools", "manager_node")

    # if the conditional node directs to planner_node, it means the manager_node has determined that the task needs to be delegated to the planner agent.
    graph.add_edge("planner", "manager_node")
    global lgapp
    lgapp = graph.compile()
    logger.info(lgapp.get_graph().draw_ascii())
    return lgapp


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

    app.state.agent = await build_graph(redis_client)

    yield
    logger.info("server shutdown initiated..")


def validate_api_key(api_key: str = Security(header_scheme), request: Request = None):
    
    logger.info("validating route %s", request.url.path)
    
    if request and request.url.path in PUBLIC_ROUTES:
        logger.info("public route accessed, skipping API key validation")
        return None
    
    if not api_key or api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )

    return None


def get_redis_client(request: Request):
    return request.app.state.redis_client


app = FastAPI(
    lifespan=lifespan,
    description="Manager AI Agent with access to Poker tournament schedules. it can delegate tasks to the Planner Agent for event search and planning.",
    dependencies=[Depends(validate_api_key)],
)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    logger.info("current date time is %s", str(datetime.datetime.now()))
    return {"name": "Manager", "status": "healthy", "datetime": str(datetime.datetime.now())}


@app.post("/chat", summary="Chat with Calendar/Planner agent")
async def chat(
    body: ChatModel,
    redis: redis.Redis = Depends(get_redis_client),
):
    logger.info("request received %s", body)
    # retrieve app state for the email and thread id
    current_state: AppState = get_appstate(body.email, body.thread_id, redis)
    # logger.info("retrieved app state %s", current_state)
    history = current_state.messages or []
    # add current user message to the history
    messages = history + [HumanMessage(content=body.content)]

    # update app state
    # invoke LLM
    new_state = await lgapp.ainvoke(
        AppState(messages=messages, thread_id=body.thread_id, email=body.email)
    )
    # logger.info("response from llm %s, type %s", new_state, type(new_state))

    # persist app state back to redis
    save_appstate(new_state, redis)
    
    # persist conversation history as well

    logger.info("final response %s", new_state["messages"][-1].content)
    
    response: ChatModel = ChatModel(
        content=new_state["messages"][-1].content,
        thread_id=body.thread_id,
        email=body.email,
        timestampInUtcMillis=int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000),
        role="assistant"
    )

    return response

