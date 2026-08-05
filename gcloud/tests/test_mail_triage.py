from unittest.mock import MagicMock

from models import MailMessage
from triage import mail_triage


def _mail(message_id="m1", sender="Bank <alerts@bank.com>", subject="UPI Alert", body="body") -> MailMessage:
    return MailMessage(
        message_id=message_id,
        subject=subject,
        sender=sender,
        body=body,
        received_on="Mon, 3 Aug 2026 00:00:00 +0000",
    )


def test_process_new_mails_passes_learned_preferences_to_classifier(monkeypatch):
    monkeypatch.setattr(mail_triage.memory_store, "get_preferences", MagicMock(return_value=["pref1"]))
    monkeypatch.setattr(mail_triage.memory_store, "get_rule", MagicMock(return_value=None))
    monkeypatch.setattr(mail_triage.memory_store, "log_action", MagicMock())
    classify_mock = MagicMock(return_value={"category": "transactional", "action": "keep", "reason": "r"})
    monkeypatch.setattr(mail_triage.llm_classifier, "classify_email", classify_mock)

    mail_triage.process_new_mails([_mail()])

    mail = classify_mock.call_args[0][0]
    assert mail.message_id == "m1"
    assert classify_mock.call_args[0][1] == ["pref1"]


def test_process_new_mails_saves_pending_with_body_for_delete_suggestion(monkeypatch):
    monkeypatch.setattr(mail_triage.memory_store, "get_preferences", MagicMock(return_value=[]))
    monkeypatch.setattr(mail_triage.memory_store, "get_rule", MagicMock(return_value=None))
    save_pending_mock = MagicMock()
    monkeypatch.setattr(mail_triage.memory_store, "save_pending", save_pending_mock)
    monkeypatch.setattr(mail_triage.telegram_bot, "send_confirmation", MagicMock())
    monkeypatch.setattr(
        mail_triage.llm_classifier,
        "classify_email",
        MagicMock(return_value={"category": "transactional", "action": "delete", "reason": "small amount"}),
    )

    mail_triage.process_new_mails([_mail(body="debited Rs 50")])

    save_pending_mock.assert_called_once_with(
        "m1", "alerts@bank.com", "UPI Alert", "transactional", "small amount", "debited Rs 50"
    )


def test_confirmation_on_transactional_mail_generalizes_into_a_preference_not_a_blanket_rule(monkeypatch):
    monkeypatch.setattr(
        mail_triage.memory_store,
        "pop_pending",
        MagicMock(
            return_value={
                "sender": "alerts@bank.com",
                "subject": "UPI Alert",
                "category": "transactional",
                "reason": "small amount",
                "body": "debited Rs 50 from account ending 934",
            }
        ),
    )
    monkeypatch.setattr(mail_triage.gmail_auth, "trash_message", MagicMock())
    monkeypatch.setattr(mail_triage.memory_store, "log_action", MagicMock())
    monkeypatch.setattr(mail_triage.telegram_bot, "answer_callback", MagicMock())
    save_rule_mock = MagicMock()
    monkeypatch.setattr(mail_triage.memory_store, "save_rule", save_rule_mock)
    add_preference_mock = MagicMock()
    monkeypatch.setattr(mail_triage.memory_store, "add_preference", add_preference_mock)
    summarize_mock = MagicMock(return_value="Delete UPI alerts for account ending 934 under Rs 2000")
    monkeypatch.setattr(mail_triage.llm_classifier, "summarize_preference", summarize_mock)

    mail_triage.handle_telegram_callback("del:m1", "cb1")

    summarize_mock.assert_called_once_with(
        "alerts@bank.com", "UPI Alert", "debited Rs 50 from account ending 934", "transactional", "delete"
    )
    add_preference_mock.assert_called_once_with("Delete UPI alerts for account ending 934 under Rs 2000")
    save_rule_mock.assert_not_called()


def test_confirmation_on_non_transactional_mail_still_saves_a_blanket_rule(monkeypatch):
    monkeypatch.setattr(
        mail_triage.memory_store,
        "pop_pending",
        MagicMock(
            return_value={
                "sender": "promo@shop.com",
                "subject": "50% off",
                "category": "promotional",
                "reason": "promo",
                "body": "",
            }
        ),
    )
    monkeypatch.setattr(mail_triage.gmail_auth, "trash_message", MagicMock())
    monkeypatch.setattr(mail_triage.memory_store, "log_action", MagicMock())
    monkeypatch.setattr(mail_triage.telegram_bot, "answer_callback", MagicMock())
    save_rule_mock = MagicMock()
    monkeypatch.setattr(mail_triage.memory_store, "save_rule", save_rule_mock)
    add_preference_mock = MagicMock()
    monkeypatch.setattr(mail_triage.memory_store, "add_preference", add_preference_mock)
    summarize_mock = MagicMock()
    monkeypatch.setattr(mail_triage.llm_classifier, "summarize_preference", summarize_mock)

    mail_triage.handle_telegram_callback("del:m1", "cb1")

    save_rule_mock.assert_called_once_with(
        "promo@shop.com", "promotional", "delete", reason="user confirmed via telegram"
    )
    add_preference_mock.assert_not_called()
    summarize_mock.assert_not_called()
