import logging
from datetime import date
from email.utils import parseaddr

from gmail import auth as gmail_auth
from llm import classifier as llm_classifier
from telegram import bot as telegram_bot
from triage import memory_store
from models import MailMessage

logger = logging.getLogger(__name__)


def _sender_email(raw_sender: str) -> str:
    _, email_address = parseaddr(raw_sender)
    return email_address.lower() or raw_sender


def process_new_mails(mails: list[MailMessage]) -> None:
    preferences = memory_store.get_preferences()
    for mail in mails:
        sender = _sender_email(mail.sender)
        classification = llm_classifier.classify_email(mail, preferences)
        category = classification["category"]
        action = classification["action"]
        reason = classification["reason"]

        rule = memory_store.get_rule(sender, category)
        if rule is not None:
            if rule["action"] == "delete":
                gmail_auth.trash_message(mail.message_id)
            memory_store.log_action(sender, mail.subject, category, rule["action"], source="rule")
            logger.info(
                "Applied remembered rule for %s/%s: %s", sender, category, rule["action"]
            )
            continue

        if action == "keep":
            memory_store.log_action(sender, mail.subject, category, "keep", source="llm_auto_keep")
            continue

        memory_store.save_pending(mail.message_id, sender, mail.subject, category, reason, mail.body)
        telegram_bot.send_confirmation(mail.message_id, sender, mail.subject, reason)
        logger.info("Sent Telegram confirmation for mail %s (%s/%s)", mail.message_id, sender, category)


def handle_telegram_callback(callback_data: str, callback_query_id: str) -> None:
    action, _, message_id = callback_data.partition(":")
    if action not in ("del", "keep") or not message_id:
        logger.warning("Unrecognized Telegram callback data: %s", callback_data)
        return

    pending = memory_store.pop_pending(message_id)
    if pending is None:
        telegram_bot.answer_callback(callback_query_id, "This request has expired.")
        return

    resolved_action = "delete" if action == "del" else "keep"
    if resolved_action == "delete":
        gmail_auth.trash_message(message_id)

    category = pending["category"]
    if category == "transactional":
        # Sender+category is too coarse for transactional mail -- the same
        # sender's transactional mail can need different actions (e.g. a
        # small-amount alert vs. a large transfer). Generalize this specific
        # confirmation into a reusable rule instead, fed back into future
        # LLM classification via classify_email's `preferences` argument.
        rule_text = llm_classifier.summarize_preference(
            pending["sender"], pending["subject"], pending.get("body", ""), category, resolved_action
        )
        memory_store.add_preference(rule_text)
    else:
        memory_store.save_rule(
            pending["sender"], category, resolved_action, reason="user confirmed via telegram"
        )
    memory_store.log_action(
        pending["sender"],
        pending["subject"],
        category,
        resolved_action,
        source=f"confirmed_{resolved_action}",
    )
    telegram_bot.answer_callback(callback_query_id, f"{resolved_action.capitalize()}d")
    logger.info(
        "Resolved confirmation for %s: %s (%s/%s)",
        message_id,
        resolved_action,
        pending["sender"],
        category,
    )


def send_daily_summary() -> None:
    actions = memory_store.get_and_clear_daily_actions(date.today())
    if not actions:
        return

    deleted = [a for a in actions if a["action"] == "delete"]
    kept = [a for a in actions if a["action"] == "keep"]

    lines = [f"📬 Daily mail digest — {len(actions)} mail(s) processed"]
    lines.append(f"\nDeleted ({len(deleted)}):")
    for a in deleted:
        lines.append(f"  - {a['sender']}: {a['subject']}")
    lines.append(f"\nKept ({len(kept)}):")
    for a in kept:
        lines.append(f"  - {a['sender']}: {a['subject']}")

    telegram_bot.send_message("\n".join(lines))
