import os

from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:e4b")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

DAILY_SUMMARY_TIME = os.environ.get("DAILY_SUMMARY_TIME", "21:00")
# Gmail watch subscriptions expire after ~7 days; renewing weekly (well within
# that window) is enough, so this runs on a fixed day+time rather than daily.
GMAIL_WATCH_RENEWAL_DAY = os.environ.get("GMAIL_WATCH_RENEWAL_DAY", "sat")
GMAIL_WATCH_RENEWAL_TIME = os.environ.get("GMAIL_WATCH_RENEWAL_TIME", "11:00")

# Auth for the endpoints in security.py -- see that module for how each is used.
API_KEY = os.environ.get("API_KEY")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET")
PUBSUB_OIDC_AUDIENCE = os.environ.get("PUBSUB_OIDC_AUDIENCE")
PUBSUB_OIDC_SERVICE_ACCOUNT_EMAIL = os.environ.get("PUBSUB_OIDC_SERVICE_ACCOUNT_EMAIL")
