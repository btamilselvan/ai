FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

COPY . .

RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "main.py"]

# CMD ["uv", "run", "main.py", "dev", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]