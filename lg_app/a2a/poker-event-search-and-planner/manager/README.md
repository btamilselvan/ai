-- uv add langgraph grandalf
-- uv pip install langgraph-cli "langgraph-cli[inmem]"
-- langgraph dev
-- langgraph-api is required to use A2A
-- Langgraph automatically exposes agent-card endpoint.
-- http://127.0.0.1:2024/.well-known/agent-card.json?assistant_id={assistant_id}
-- https://reference.langchain.com/python/langgraph.prebuilt/tool_node/tools_condition


## Run

```bash
# Development
uv run uvicorn main:app --reload --host 0.0.0.0 --port 9001
uv run uvicorn poker_agent.main:app --reload --host 0.0.0.0 --port 9001

# Production
uv run gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:9001

# Direct
uv run main.py
```
