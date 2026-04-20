from fastmcp.tools import tool
from fastmcp.dependencies import CurrentRequest
from fastmcp import Context
from starlette.requests import Request
import logging

logger = logging.getLogger(__name__)


@tool(name="search")
async def collection_search(query: str, context: Context, request: Request = CurrentRequest()) -> list[dict]:
    pass
