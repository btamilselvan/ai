from state.app_state import AppState
from langchain_openai import OpenAI
from dotenv import load_dotenv
from typing import Literal

def manager_node(app_state: AppState) -> AppState:
    # call Manager agent to decide which node to call next
    pass

def conditional_node(app_state: AppState) -> Literal["scout", "planner", "end"]:
    # based on the app_state, decide which node to call next
    pass

def planner_node(app_state: AppState) -> AppState:
    pass