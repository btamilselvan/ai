import logging
import secrets

from fastapi import Header, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

import config

logger = logging.getLogger(__name__)

# Reused across calls -- google-auth's Request wraps a requests.Session and is
# meant to be reused rather than constructed per verification.
_google_request = google_requests.Request()


def require_api_key(x_api_key: str = Header(default=None)) -> None:
    """Guards manually-triggered admin endpoints (e.g. /gmail/renew-watch)."""
    if not config.API_KEY or not x_api_key or not secrets.compare_digest(x_api_key, config.API_KEY):
        logger.warning("Rejected request: missing or invalid X-API-Key")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing API key")


def verify_telegram_secret(x_telegram_bot_api_secret_token: str = Header(default=None)) -> None:
    """Guards /telegram-webhook using the secret_token registered via setWebhook.

    Telegram echoes this back as the X-Telegram-Bot-Api-Secret-Token header on
    every webhook request -- see https://core.telegram.org/bots/api#setwebhook.
    """
    if (
        not config.TELEGRAM_WEBHOOK_SECRET
        or not x_telegram_bot_api_secret_token
        or not secrets.compare_digest(x_telegram_bot_api_secret_token, config.TELEGRAM_WEBHOOK_SECRET)
    ):
        logger.warning("Rejected request: missing or invalid Telegram secret token")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Telegram secret token")


def verify_pubsub_oidc_token(authorization: str = Header(default=None)) -> None:
    """Guards /webhook using Google's signed OIDC token for authenticated Pub/Sub push.

    See https://docs.cloud.google.com/pubsub/docs/authenticate-push-subscriptions --
    the push subscription is configured with a service account, and Pub/Sub attaches
    a bearer token signed by Google on every push request.
    """
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Rejected Pub/Sub push request: missing bearer token")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = authorization.removeprefix("Bearer ")
    try:
        # Validates signature, expiry, and issuer against Google's public certs,
        # and that the token's audience matches ours.
        claims = id_token.verify_oauth2_token(token, _google_request, audience=config.PUBSUB_OIDC_AUDIENCE)
    except ValueError as e:
        logger.warning("Rejected Pub/Sub push request: invalid OIDC token: %s", e)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from e

    # Audience alone isn't enough -- pin the token to our specific push service
    # account so a different token sharing the same audience can't be replayed.
    if claims.get("email") != config.PUBSUB_OIDC_SERVICE_ACCOUNT_EMAIL:
        logger.warning("Rejected Pub/Sub push request: unexpected token subject %s", claims.get("email"))
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unexpected token subject")
