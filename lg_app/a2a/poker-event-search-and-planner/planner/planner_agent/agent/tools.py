from langchain_core.tools import tool


@tool(description="Tool that gets the current datetime according to the calendar timezone.")
def get_current_datetime():
    """Returns current datetime according to the calendar timezone"""
    pass


@tool(
    description="Tool that get information about the calendars in Google Calendar."
)
def get_calendar_info():
    pass


@tool(
    description="Use this tool to search for events in Google Calendar",
    args_schema={
        "min_datetime": {
            "name": "min_datetime",
            "type": "string",
            "description": "The start datetime for the events in 'YYYY-MM-DD HH:MM:SS' format.",
        },
        "max_datetime": {
            "name": "max_datetime",
            "type": "string",
            "description": "The end datetime for the events in 'YYYY-MM-DD HH:MM:SS' format.",
        },
        "single_events": {
            "name": "single_events",
            "type": "boolean",
            "default": True,
            "description": "Whether to expand recurring events into instances and only return single one-off events and instances of recurring events.'startTime' or 'updated'.",
        },
        "query": {
            "name": "query",
            "default": None,
            "type": list[str],
            "description": "Free text search terms to find events, that match these terms in the following fields: summary, description, location, attendee's displayName, attendee's email, organizer's displayName, organizer's email.",
        },
    },
)

@tool(description="Tool that retrieves events from Google Calendar.")
def search_events(min_datetime, max_datetime):
    pass
