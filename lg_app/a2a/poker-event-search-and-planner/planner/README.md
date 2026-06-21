### Code Sample

build credentials using,

```
credentials = service_account.Credentials.from_service_account_file(
    os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    scopes=["https://www.googleapis.com/auth/calendar"]
)
```
build api_resource using the credentials
```
api_resource = build("calendar", "v3", credentials=credentials)
```

then call calendar REST endpoint using
```
api_resource.events().list(
    calendarId=calendar_id,
    maxResults=10,
    singleEvents=True,
    orderBy="startTime"
).execute()
```
the above python call maps directly to the REST endpoint:
```
GET https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events
```
and every keyword argument you pass to .list() corresponds to a query parameter documented in
```https://developers.google.com/workspace/calendar/api/v3/reference/events/get``` page.


### Run

```bash
# Development
uv run uvicorn main:app --reload --host 0.0.0.0 --port 9000
uv run uvicorn planner_agent.main:app --reload --host 0.0.0.0 --port 9000

# Production
uv run gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:9000

# Direct
uv run main.py
```

#### Refernces

- https://docs.langchain.com/oss/python/integrations/providers/overview
- https://reference.langchain.com/python/langchain-google-community
- https://medium.com/@dikshitkumar951/transform-your-scheduling-experience-building-a-personal-booking-agent-with-langgraph-part-1-6ba05df2028a
- https://reference.langchain.com/python/langchain-google-community/calendar/toolkit
- https://reference.langchain.com/python/langchain-google-community/calendar/toolkit/CalendarToolkit

