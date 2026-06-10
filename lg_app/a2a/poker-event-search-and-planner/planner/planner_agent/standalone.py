import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[logging.StreamHandler()],
)

from planner_agent.main import build_graph
from planner_agent.util.app_state import AppState
from langchain_core.messages import HumanMessage
import asyncio

logger = logging.getLogger(__name__)

agent = asyncio.run(build_graph())

if __name__ == "__main__":
    # Run the agent with an initial state
    initial_state = AppState(
        messages=[
            HumanMessage(content="Do I have anything scheduled for June 15th, 2026?")
        ],
    )
    final_state = agent.invoke(initial_state)
    logger.info(f"Final state: {final_state}")
