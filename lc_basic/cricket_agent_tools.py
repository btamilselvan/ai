from langchain.tools import tool


@tool("get_upcoming_cricket_matches", response_format="content", description="Fetch information about upcoming cricket matches.")
def get_upcoming_cricket_matches():
    """ 
    This is a placeholder function that simulates fetching upcoming cricket matches.
    In a real implementation, this function would fetch data from a cricket API or database. 
    """

    return [
        {
            "series": "ICC World Cup 2026",
            "match_desc": "42nd Match, Super 8 Group 2 (Y1 v Y4)",
            "match_format": "T20",
            "start_date": "1771752600000",
            "end_date": "1771804799000",
            "team1": "England",
            "team2": "Sri Lanka",
            "venue": "Pallekele International Cricket Stadium"
        },
        {
            "series": "ICC World Cup 2026",
            "match_desc": "43rd Match, Super 8 Group 1 (X1 v X4)",
            "match_format": "T20",
            "start_date": "1771767000000",
            "end_date": "1771804799000",
            "team1": "India",
            "team2": "South Africa",
            "venue": "Narendra Modi Stadium"
        }
    ]
