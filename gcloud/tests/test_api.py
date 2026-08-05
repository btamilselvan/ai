import base64
import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import api
from models import MailMessage


@pytest.fixture
def client():
    with TestClient(api.app) as c:
        yield c


def _pubsub_payload(data: dict | None = None, raw_data: str | None = None) -> dict:
    encoded = raw_data if raw_data is not None else base64.b64encode(json.dumps(data).encode()).decode()
    return {
        "message": {
            "data": encoded,
            "messageId": "1",
            "publishTime": "2026-08-03T00:00:00Z",
        },
        "subscription": "projects/test-project/subscriptions/test-sub",
    }


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_acks_and_triggers_mail_triage(client, monkeypatch):
    fake_mail = MailMessage(
        message_id="abc123",
        subject="Test subject",
        sender="sender@example.com",
        body="hello",
        received_on="Mon, 3 Aug 2026 00:00:00 +0000",
    )
    fetch_mails_mock = MagicMock(return_value=[fake_mail])
    process_new_mails_mock = MagicMock()
    monkeypatch.setattr(api, "fetch_mails", fetch_mails_mock)
    monkeypatch.setattr(api.mail_triage, "process_new_mails", process_new_mails_mock)

    payload = _pubsub_payload({"emailAddress": "me@example.com", "historyId": "12345"})
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    # TestClient runs BackgroundTasks to completion before returning, so the
    # triage pipeline should already have been invoked with the decoded historyId.
    fetch_mails_mock.assert_called_once_with("12345")
    process_new_mails_mock.assert_called_once_with([fake_mail])


def test_webhook_survives_triage_errors(client, monkeypatch):
    # A failure inside the background task must not surface as a request error,
    # since the response has already been sent by the time it runs.
    monkeypatch.setattr(api, "fetch_mails", MagicMock(side_effect=RuntimeError("boom")))

    payload = _pubsub_payload({"emailAddress": "me@example.com", "historyId": "12345"})
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "success"}


def test_webhook_malformed_base64_returns_500(client):
    payload = _pubsub_payload(raw_data="a")  # invalid base64 padding

    response = client.post("/webhook", json=payload)

    assert response.status_code == 500


def test_webhook_missing_history_id_returns_500(client):
    payload = _pubsub_payload({"emailAddress": "me@example.com"})  # no historyId

    response = client.post("/webhook", json=payload)

    assert response.status_code == 500


def test_renew_gmail_watch_success_does_not_alert(monkeypatch):
    monkeypatch.setattr(api, "renew_watch", MagicMock(return_value={"historyId": "1", "expiration": "999"}))
    send_message_mock = MagicMock()
    monkeypatch.setattr(api.telegram_bot, "send_message", send_message_mock)

    api._renew_gmail_watch()

    send_message_mock.assert_not_called()


def test_renew_gmail_watch_failure_sends_telegram_alert(monkeypatch):
    monkeypatch.setattr(api, "renew_watch", MagicMock(return_value=None))
    send_message_mock = MagicMock()
    monkeypatch.setattr(api.telegram_bot, "send_message", send_message_mock)

    api._renew_gmail_watch()

    send_message_mock.assert_called_once()


def test_renew_watch_endpoint_success(client, monkeypatch):
    monkeypatch.setattr(
        api, "renew_watch", MagicMock(return_value={"historyId": "42", "expiration": "1234567890"})
    )

    response = client.post("/gmail/renew-watch")

    assert response.status_code == 200
    assert response.json() == {"status": "success", "historyId": "42", "expiration": "1234567890"}


def test_renew_watch_endpoint_failure_returns_502(client, monkeypatch):
    monkeypatch.setattr(api, "renew_watch", MagicMock(return_value=None))

    response = client.post("/gmail/renew-watch")

    assert response.status_code == 502
