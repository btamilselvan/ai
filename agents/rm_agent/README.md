
## Build commands
- uv run uvicorn main:app --reload --host 0.0.0.0 --port 9000
- uv run main.py
- uv run gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:9000

### References
- https://api-docs.deepseek.com
- https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html