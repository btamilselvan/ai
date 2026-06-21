import redis
from planner_agent.util.app_state import AppState
import logging
import json

logger = logging.getLogger(__name__)


def get_appstate(email, thread_id, r: redis.Redis):
    """retrieve app state for the given email and thread_id or create one if does not exist"""
    app_state = r.json().get(f"{email}:{thread_id}")

    logger.info(
        "retrieved app state %s, thread %s email %s", app_state, thread_id, email
    )

    if app_state:
        return AppState.model_validate_json(app_state)
    else:
        return AppState(thread_id=thread_id, email=email)


def save_appstate(state: dict, r):
    appstate = AppState(**state)

    r.json().set(
        f"{appstate.email}:{appstate.thread_id}", "$", appstate.model_dump_json()
    )
    # logger.info("app state saved to redis %s", appstate)
