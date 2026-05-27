from pydantic import BaseModel
from typing import Optional

class PokerTournament(BaseModel):
    name: str
    start_date: str
    end_date: str
    location: Optional[str] = None
    prize_pool: str
    buy_in: str


class TouranamentsResponse(BaseModel):
    tournaments: list[PokerTournament]
