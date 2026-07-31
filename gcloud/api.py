import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[logging.StreamHandler()],
)

import base64
import json
from fastapi import FastAPI, HTTPException, Query, status, Request
from pydantic import BaseModel
from gmail_auth import get_credentials, fetch_mails

logger = logging.getLogger(__name__)

app = FastAPI()

# Change this to a long, secure passphrase of your choice
MY_SECRET_TOKEN = "YOUR_CHOSEN_SECRET_PASSPHRASE"


# Define the expected Google Pub/Sub request schema
class PubSubMessage(BaseModel):
    data: str  # Base64 encoded string from Google
    messageId: str
    publishTime: str


class PubSubPayload(BaseModel):
    message: PubSubMessage
    subscription: str


@app.get("/health")
async def health_check():
    logger.info("health check")
    return {"status": "ok"}


@app.post("/webhook")
async def gmail_webhook(payload: PubSubPayload):
    # 1. Verify the secret token matches
    # if token != MY_SECRET_TOKEN:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Unauthorized request source"
    #     )

    try:
        # 2. Decode the base64 data envelope from Google
        base64_data = payload.message.data
        decoded_bytes = base64.b64decode(base64_data)
        decoded_str = decoded_bytes.decode("utf-8")

        # 3. Parse the JSON inside the payload
        gmail_event = json.loads(decoded_str)

        # This will contain 'emailAddress' and 'historyId'
        logger.info(
            "📧 Email Address: %s, historyId: %s",
            gmail_event["emailAddress"],
            gmail_event["historyId"],
        )

        mails = fetch_mails(gmail_event["historyId"])

        # logger.info("fetched mails %s", mails)

        # 4. Return 200 OK so Google acknowledges successful receipt
        return {"status": "success"}

    except Exception as e:
        logger.exception("❌ Error processing message: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error parsing webhook payload",
        )
