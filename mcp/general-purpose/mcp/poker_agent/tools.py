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
from poker_tournament_mock import generate_mock_tournaments
from datetime import datetime

logger = logging.getLogger(__name__)

load_dotenv()

mock_tournaments = generate_mock_tournaments(num_events=100)

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
    
    # convert date strings to date
    search_start = datetime.strptime(start_date, "%Y-%m-%d").date()
    search_end = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    
    results = []
    for t in mock_tournaments:
        t_start = datetime.strptime(t.start_date, "%Y-%m-%d").date()
        t_end = datetime.strptime(t.end_date, "%Y-%m-%d").date()
        is_in_range = (t_start >= search_start) and (t_end <= search_end)
        
        if is_in_range:
            
            if location:
                if location.lower() in t.location.lower():
                    results.append(t)
            else:
                results.append(t)
                
    
    return TouranamentsResponse(
        tournaments=results
    )
