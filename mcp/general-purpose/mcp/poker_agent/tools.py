from fastmcp.tools import tool
import httpx
import logging
import os
from dotenv import load_dotenv
from pydantic import Field
from typing import Annotated, Optional
from contextlib import asynccontextmanager
from fastmcp.dependencies import Depends
import resource_registry
from models import PokerTournament, TouranamentsResponse

logger = logging.getLogger(__name__)

load_dotenv()


@tool(
    name="do_poker_tournament_search",
    description="Search for poker tournaments based on date and location"
)
async def do_poker_tournament_search(start_date: Annotated[str, Field(description="The start date for the search (e.g., '2026-05-10')",)],
                                     end_date: Annotated[Optional[str],
                                                         Field(description="The end date for the search (e.g., '2026-10-10')", default=None)],
                                     location: Annotated[Optional[str],
                                                         Field(description="The location of the tournaments (e.g., 'Las Vegas')", default=None)]) -> TouranamentsResponse:
    logger.debug("Performing poker tournament search with start_date: %s, end_date: %s, location: %s",
                 start_date, end_date, location)
    return TouranamentsResponse(
        tournaments=[
            PokerTournament(
                name="Poker Tournament 1",
                start_date="2026-05-15",
                end_date="2026-05-15",
                location=location,
                prize_pool="$10,000",
                buy_in="$100"
            ),
            PokerTournament(
                name="Poker Tournament 2",
                start_date="2026-12-20",
                end_date="2026-12-20",
                location=location,
                prize_pool="$15,000",
                buy_in="$150"
            )
        ]
    )
