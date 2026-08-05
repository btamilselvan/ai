import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(filename)s: %(lineno)d] [Thread-%(thread)d] %(message)s",
    handlers=[logging.StreamHandler()],
)

import base64
import json
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, status, Request
from pydantic import BaseModel

import config
from gmail.auth import fetch_mails, renew_watch
from telegram import bot as telegram_bot
from triage import mail_triage

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _renew_gmail_watch() -> None:
    response = renew_watch()
    if response is None:
        logger.error("❌ Gmail watch renewal failed; push notifications may lapse soon")
        try:
            telegram_bot.send_message(
                "⚠️ Failed to renew Gmail watch subscription — check logs, "
                "push notifications may stop working within 7 days."
            )
        except Exception:
            logger.exception("❌ Also failed to send Telegram alert about watch renewal failure")


@asynccontextmanager
async def lifespan(app: FastAPI):
    summary_hour, summary_minute = config.DAILY_SUMMARY_TIME.split(":")
    scheduler.add_job(
        mail_triage.send_daily_summary,
        CronTrigger(hour=int(summary_hour), minute=int(summary_minute)),
    )
    watch_hour, watch_minute = config.GMAIL_WATCH_RENEWAL_TIME.split(":")
    scheduler.add_job(
        _renew_gmail_watch,
        CronTrigger(
            day_of_week=config.GMAIL_WATCH_RENEWAL_DAY,
            hour=int(watch_hour),
            minute=int(watch_minute),
        ),
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

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


@app.post("/gmail/renew-watch")
async def gmail_renew_watch():
    response = renew_watch()
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gmail watch renewal failed, check server logs",
        )
    return {
        "status": "success",
        "historyId": response.get("historyId"),
        "expiration": response.get("expiration"),
    }


def _fetch_and_triage(history_id: str) -> None:
    try:
        mails = fetch_mails(history_id)
        mail_triage.process_new_mails(mails)
    except Exception as e:
        logger.exception("❌ Error triaging mail for historyId %s: %s", history_id, e)


@app.post("/webhook")
async def gmail_webhook(payload: PubSubPayload, background_tasks: BackgroundTasks):
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

        # 4. Fetch + classify mail in the background so Pub/Sub gets acked
        # immediately instead of waiting on Gmail/LLM/Telegram round-trips.
        background_tasks.add_task(_fetch_and_triage, gmail_event["historyId"])

        # 5. Return 200 OK so Google acknowledges successful receipt
        return {"status": "success"}

    except Exception as e:
        logger.exception("❌ Error processing message: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error parsing webhook payload",
        )


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    callback_query = update.get("callback_query")

    if not callback_query:
        return {"status": "ignored"}

    try:
        mail_triage.handle_telegram_callback(callback_query["data"], callback_query["id"])
        return {"status": "success"}
    except Exception as e:
        logger.exception("❌ Error processing telegram callback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error parsing telegram webhook payload",
        )
