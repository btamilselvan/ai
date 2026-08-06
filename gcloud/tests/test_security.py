from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import api
import config
import security


# --- require_api_key --------------------------------------------------------


def test_require_api_key_rejects_missing_header(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "correct-key")
    with pytest.raises(HTTPException) as exc_info:
        security.require_api_key(x_api_key=None)
    assert exc_info.value.status_code == 401


def test_require_api_key_rejects_wrong_value(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "correct-key")
    with pytest.raises(HTTPException) as exc_info:
        security.require_api_key(x_api_key="wrong-key")
    assert exc_info.value.status_code == 401


def test_require_api_key_accepts_correct_value(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "correct-key")
    security.require_api_key(x_api_key="correct-key")  # does not raise


def test_require_api_key_rejects_when_unconfigured(monkeypatch):
    # An unset API_KEY must not make the check a no-op.
    monkeypatch.setattr(config, "API_KEY", None)
    with pytest.raises(HTTPException) as exc_info:
        security.require_api_key(x_api_key="anything")
    assert exc_info.value.status_code == 401


# --- verify_telegram_secret --------------------------------------------------


def test_verify_telegram_secret_rejects_missing_header(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_WEBHOOK_SECRET", "tg-secret")
    with pytest.raises(HTTPException) as exc_info:
        security.verify_telegram_secret(x_telegram_bot_api_secret_token=None)
    assert exc_info.value.status_code == 401


def test_verify_telegram_secret_rejects_wrong_value(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_WEBHOOK_SECRET", "tg-secret")
    with pytest.raises(HTTPException) as exc_info:
        security.verify_telegram_secret(x_telegram_bot_api_secret_token="wrong")
    assert exc_info.value.status_code == 401


def test_verify_telegram_secret_accepts_correct_value(monkeypatch):
    monkeypatch.setattr(config, "TELEGRAM_WEBHOOK_SECRET", "tg-secret")
    security.verify_telegram_secret(x_telegram_bot_api_secret_token="tg-secret")  # does not raise


# --- verify_pubsub_oidc_token -------------------------------------------------


def test_verify_pubsub_oidc_token_rejects_missing_header():
    with pytest.raises(HTTPException) as exc_info:
        security.verify_pubsub_oidc_token(authorization=None)
    assert exc_info.value.status_code == 401


def test_verify_pubsub_oidc_token_rejects_non_bearer_header():
    with pytest.raises(HTTPException) as exc_info:
        security.verify_pubsub_oidc_token(authorization="Basic abc123")
    assert exc_info.value.status_code == 401


def test_verify_pubsub_oidc_token_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(
        security.id_token, "verify_oauth2_token", MagicMock(side_effect=ValueError("bad token"))
    )
    with pytest.raises(HTTPException) as exc_info:
        security.verify_pubsub_oidc_token(authorization="Bearer bad-token")
    assert exc_info.value.status_code == 401


def test_verify_pubsub_oidc_token_rejects_unexpected_service_account(monkeypatch):
    monkeypatch.setattr(config, "PUBSUB_OIDC_SERVICE_ACCOUNT_EMAIL", "pusher@my-project.iam.gserviceaccount.com")
    monkeypatch.setattr(
        security.id_token,
        "verify_oauth2_token",
        MagicMock(return_value={"email": "someone-else@other-project.iam.gserviceaccount.com"}),
    )
    with pytest.raises(HTTPException) as exc_info:
        security.verify_pubsub_oidc_token(authorization="Bearer valid-jwt")
    assert exc_info.value.status_code == 401


def test_verify_pubsub_oidc_token_accepts_expected_service_account(monkeypatch):
    monkeypatch.setattr(config, "PUBSUB_OIDC_SERVICE_ACCOUNT_EMAIL", "pusher@my-project.iam.gserviceaccount.com")
    verify_mock = MagicMock(return_value={"email": "pusher@my-project.iam.gserviceaccount.com"})
    monkeypatch.setattr(security.id_token, "verify_oauth2_token", verify_mock)

    security.verify_pubsub_oidc_token(authorization="Bearer valid-jwt")  # does not raise

    verify_mock.assert_called_once()
    assert verify_mock.call_args[0][0] == "valid-jwt"


# --- end-to-end wiring: protected routes reject unauthenticated requests -----


@pytest.fixture
def unauthenticated_client():
    # Deliberately no dependency_overrides -- proves api.py actually applies
    # each dependency, not just that the functions work in isolation.
    with TestClient(api.app) as c:
        yield c


def test_renew_watch_endpoint_requires_api_key(unauthenticated_client):
    response = unauthenticated_client.post("/gmail/renew-watch")
    assert response.status_code == 401


def test_webhook_endpoint_requires_oidc_token(unauthenticated_client):
    response = unauthenticated_client.post(
        "/webhook",
        json={
            "message": {"data": "", "messageId": "1", "publishTime": "2026-08-05T00:00:00Z"},
            "subscription": "projects/test-project/subscriptions/test-sub",
        },
    )
    assert response.status_code == 401


def test_telegram_webhook_endpoint_requires_secret_token(unauthenticated_client):
    response = unauthenticated_client.post("/telegram-webhook", json={})
    assert response.status_code == 401


def test_health_check_requires_no_auth(unauthenticated_client):
    response = unauthenticated_client.get("/health")
    assert response.status_code == 200
