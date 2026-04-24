from fastmcp.tools import tool
import httpx
import logging
import os
from dotenv import load_dotenv
from pydantic import Field
from typing import Annotated
from contextlib import asynccontextmanager
from fastmcp.dependencies import Depends
import resource_registry

logger = logging.getLogger(__name__)

load_dotenv()

PERM_TRACKER_API_URL = os.getenv("PERM_TRACKER_API_URL")


# @asynccontextmanager
# async def get_http_client():
#     http_client = httpx.AsyncClient()
#     logger.debug("created http client: %s", http_client)
#     yield http_client
#     await http_client.aclose()


@tool(
    name="get_current_gc_perm_estimate",
    description="Get the current green card perm application approval estimate from external service"
)
async def get_current_gc_perm_estimate(submission_date: Annotated[str, Field(description="The date submitted (e.g., '2025-10-10')")],
                                       employer_first_letter: Annotated[str, Field(description="First letter of the employer's name (e.g., 'A')")]) -> dict:
    """
    Estimates GC PERM processing time based on submission date and employer's first letter.

    Args:
        submission_date: The date submitted (e.g., '2025-10-10')
        employer_first_letter: First letter of the employer's name (e.g., 'A')
    """

    logger.debug("getting current gc perm estimate for submission_date: %s, employer_first_letter: %s",
                 submission_date, employer_first_letter)

    logger.debug("http client from context: %s", resource_registry.http_client)

    response = await resource_registry.http_client.post(PERM_TRACKER_API_URL, json={
        "submit_date": submission_date,
        "employer_first_letter": employer_first_letter
    })
    logger.debug("response from perm tracker api: %s", response.text)
    if response.status_code == 200:
        estimate = response.json()
        logger.debug("received gc perm estimate: %s", estimate)
        return estimate

    return {"error": "Unable to fetch gc perm estimate at the moment"}
