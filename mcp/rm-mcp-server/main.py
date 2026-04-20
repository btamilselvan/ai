from server import mcp
import uvicorn
import logging
# import hooks # noqa: F401 - required to register middleware

#configure logging
logging.basicConfig(
    level=logging.DEBUG,
    # include thread id
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[
        logging.StreamHandler()  # log to console
    ]
)
logger = logging.getLogger(__name__)

# def get_app():
#     return mcp.http_app(transport="sse")


# run the server
if __name__ == "__main__":
    pass
    # mcp.run(transport="sse")
    # uvicorn.run(mcp.http_app(transport="sse"), host="0.0.0.0", port=8002)
    # uvicorn.run("main:get_app", host="0.0.0.0", port=8002, reload=True, factory=True)

