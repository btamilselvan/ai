import json
import logging
from datetime import date, datetime

import redis

import config

logger = logging.getLogger(__name__)

PENDING_TTL_SECONDS = 3 * 24 * 60 * 60
ACTIONS_TTL_SECONDS = 2 * 24 * 60 * 60
PREFERENCES_KEY = "learned_preferences"

_client = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    decode_responses=True,
)


def _rule_key(sender: str, category: str) -> str:
    return f"rule:{sender}:{category}"


def get_rule(sender: str, category: str) -> dict | None:
    raw = _client.get(_rule_key(sender, category))
    return json.loads(raw) if raw else None


def save_rule(sender: str, category: str, action: str, reason: str) -> None:
    value = {
        "action": action,
        "reason": reason,
        "updated_at": datetime.now().isoformat(),
    }
    _client.set(_rule_key(sender, category), json.dumps(value))
    logger.info("Saved rule %s -> %s", _rule_key(sender, category), value)


def save_pending(
    message_id: str, sender: str, subject: str, category: str, reason: str, body: str | None = None
) -> None:
    value = {
        "sender": sender,
        "subject": subject,
        "category": category,
        "reason": reason,
        # Kept so a later confirmation can be generalized into a learned
        # preference (see add_preference) -- the sender/subject/category
        # alone don't carry the amount/account/alert-type signals needed.
        "body": (body or "")[:2000],
    }
    _client.set(f"pending:{message_id}", json.dumps(value), ex=PENDING_TTL_SECONDS)


def pop_pending(message_id: str) -> dict | None:
    key = f"pending:{message_id}"
    raw = _client.get(key)
    if not raw:
        return None
    _client.delete(key)
    return json.loads(raw)


def log_action(sender: str, subject: str, category: str, action: str, source: str) -> None:
    entry = {
        "time": datetime.now().isoformat(),
        "sender": sender,
        "subject": subject,
        "category": category,
        "action": action,
        "source": source,
    }
    key = f"actions:{date.today().isoformat()}"
    _client.rpush(key, json.dumps(entry))
    _client.expire(key, ACTIONS_TTL_SECONDS)


def get_and_clear_daily_actions(for_date: date) -> list[dict]:
    key = f"actions:{for_date.isoformat()}"
    entries = _client.lrange(key, 0, -1)
    _client.delete(key)
    return [json.loads(entry) for entry in entries]


def add_preference(text: str) -> None:
    _client.rpush(PREFERENCES_KEY, text)
    logger.info("Learned new preference: %s", text)


def get_preferences() -> list[str]:
    return _client.lrange(PREFERENCES_KEY, 0, -1)
