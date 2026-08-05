import logging

import httpx

import config

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


def _url(method: str) -> str:
    return f"{API_BASE}/bot{config.TELEGRAM_BOT_TOKEN}/{method}"


def send_confirmation(message_id: str, sender: str, subject: str, reason: str) -> None:
    text = (
        f"🗑 Suggested delete\n\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Reason: {reason}"
    )
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🗑 Delete", "callback_data": f"del:{message_id}"},
                {"text": "📥 Keep", "callback_data": f"keep:{message_id}"},
            ]
        ]
    }
    response = httpx.post(
        _url("sendMessage"),
        json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "reply_markup": keyboard,
        },
        timeout=30,
    )
    response.raise_for_status()


def answer_callback(callback_query_id: str, text: str) -> None:
    response = httpx.post(
        _url("answerCallbackQuery"),
        json={"callback_query_id": callback_query_id, "text": text},
        timeout=30,
    )
    response.raise_for_status()


def send_message(text: str) -> None:
    response = httpx.post(
        _url("sendMessage"),
        json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text},
        timeout=30,
    )
    response.raise_for_status()
