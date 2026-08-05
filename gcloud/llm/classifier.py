import json
import logging

import httpx

import config
from models import MailMessage

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "promotional",
    "newsletter",
    "security-alert",
    "billing",
    "transactional",
    "personal",
    "spam",
    "other",
}
VALID_ACTIONS = {"delete", "keep"}

BASE_SYSTEM_PROMPT = f"""You triage inbox email for a user. Given an email's sender, subject and body, decide:
- category: one of {sorted(VALID_CATEGORIES)}
- action: "delete" (promotional/spam/low-value noise, or transactional mail the user has said they don't
  care about) or "keep" (personal, security-related, or transactional mail that actually matters)

Transactional mail is NOT always kept -- the user has explicitly said some transactional mail (e.g.
small-amount alerts, specific accounts, routine confirmations) should be deleted. If a "Learned user
preferences" list is given below, apply any preference relevant to this email when deciding action.

Respond with ONLY a JSON object: {{"category": "<category>", "action": "delete"|"keep", "reason": "<short reason>"}}
When unsure and no learned preference applies, prefer "keep"."""

PREFERENCE_SYSTEM_PROMPT = """The user just confirmed an action (delete or keep) on an email via Telegram.
Write ONE short, reusable rule describing when to take this same action on similar future emails. Base it
on concrete signals actually present in the email (e.g. a specific amount threshold, account/card number,
transaction or alert type, sender) -- not the specific subject line, which won't repeat.
Respond with ONLY the rule sentence, no quotes, no JSON."""


def classify_email(mail: MailMessage, preferences: list[str] | None = None) -> dict:
    body = (mail.body or "")[:2000]
    user_prompt = f"From: {mail.sender}\nSubject: {mail.subject}\nBody:\n{body}"

    system_prompt = BASE_SYSTEM_PROMPT
    if preferences:
        prefs_block = "\n".join(f"- {p}" for p in preferences)
        system_prompt += f"\n\nLearned user preferences:\n{prefs_block}"

    response = httpx.post(
        f"{config.OLLAMA_HOST}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["message"]["content"]
    result = json.loads(content)

    category = result.get("category", "other")
    if category not in VALID_CATEGORIES:
        category = "other"
    action = result.get("action", "keep")
    if action not in VALID_ACTIONS:
        action = "keep"

    classification = {
        "category": category,
        "action": action,
        "reason": result.get("reason", ""),
    }
    logger.info("Classified mail %s: %s", mail.message_id, classification)
    return classification


def summarize_preference(sender: str, subject: str, body: str, category: str, action: str) -> str:
    user_prompt = (
        f"Sender: {sender}\nCategory: {category}\nSubject: {subject}\nBody:\n{(body or '')[:2000]}\n\n"
        f"Confirmed action: {action}"
    )

    response = httpx.post(
        f"{config.OLLAMA_HOST}/api/chat",
        json={
            "model": config.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": PREFERENCE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    rule = response.json()["message"]["content"].strip()
    logger.info("Generalized preference for %s/%s -> %s: %s", sender, category, action, rule)
    return rule
