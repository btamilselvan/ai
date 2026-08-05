### 

https://docs.cloud.google.com/pubsub/docs/overview

 
## Configure push notifications in Gmail API
https://developers.google.com/workspace/gmail/api/guides/push#prereqs


- 1) install gcloud cli
https://docs.cloud.google.com/sdk/docs/install-sdk
- 2) Install Pub/Sub client library
https://docs.cloud.google.com/pubsub/docs/reference/libraries#client-libraries-install-python
- 3) Enable Pub/Sub API in the gcloud console for the selected project
https://console.developers.google.com/apis/api/pubsub.googleapis.com/overview?project=<project_id>
- 4) Create Pub/Sub topic
https://docs.cloud.google.com/pubsub/docs/reference/libraries#client-libraries-install-python
- 5) Grant publish rights on the topic
https://developers.google.com/workspace/gmail/api/guides/push#grant-publish
- 6) Make a publicly accessible HTTPS URL to receive messages
    - use zrok tunnel
- 7) Create a subscribtion in the gcloud console using the publicly accessible HTTPS URL created above
- 8) Setup subscribtion authentication
https://docs.cloud.google.com/pubsub/docs/authenticate-push-subscriptions
- 7) Setup GmailClient API to call watch()
    - Enable GmailAPI in GCP
    - Setup OAuth Consent screen and use credentials.json to run gmail/auth.py
    - https://developers.google.com/workspace/gmail/api/reference/rest/v1/users/watch
    - https://developers.google.com/workspace/guides/configure-oauth-consent


## References

https://googleapis.github.io/google-api-python-client/docs/epy/googleapiclient.discovery-module.html
https://googleapis.github.io/google-api-python-client/docs/dyn/gmail_v1.users.messages.html
https://developers.google.com/workspace/gmail/api/reference/rest
https://core.telegram.org/bots/api

### RUN

uv run uvicorn api:app --host 0.0.0.0 --port 8006 --reload

## Mail triage (LLM + Telegram + memory)

New mail fetched from the webhook is classified by a local Ollama `gemma4:e4b`
model, and mail suggested for deletion is confirmed via Telegram before being
trashed. Confirmed sender+category decisions are remembered in Redis so
similar mail is auto-handled next time. A daily digest is sent to Telegram.

Setup:
- `ollama pull gemma4:e4b` and have `ollama serve` running.
- Have a Redis instance reachable.
- Create a Telegram bot via [@BotFather](https://t.me/BotFather) (if you don't
  have one already) and note its token and your chat id.
- Register the bot's webhook once (same public tunnel used for the Gmail
  Pub/Sub subscription above):
  `https://api.telegram.org/bot<TOKEN>/setWebhook?url=<PUBLIC_URL>/telegram-webhook`
- Create a `.env` file (gitignored) with:
  ```
  OLLAMA_HOST=http://localhost:11434
  OLLAMA_MODEL=gemma4:e4b
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_DB=0
  TELEGRAM_BOT_TOKEN=<your bot token>
  TELEGRAM_CHAT_ID=<your chat id>
  DAILY_SUMMARY_TIME=21:00
  GMAIL_WATCH_RENEWAL_DAY=sat
  GMAIL_WATCH_RENEWAL_TIME=11:00
  ```

## Keeping the Gmail watch alive

Gmail's `watch()` subscription expires after ~7 days. As long as the API
process is running, `api.py` schedules a weekly job (default Saturday 11:00,
via `GMAIL_WATCH_RENEWAL_DAY`/`GMAIL_WATCH_RENEWAL_TIME`) that calls
`renew_watch()` automatically, well within the 7-day window. If renewal
fails, a Telegram alert is sent so you know to check the logs before push
notifications lapse. You can also trigger a renewal on demand at any time
with `POST /gmail/renew-watch` (e.g. `curl -X POST http://localhost:8006/gmail/renew-watch`);
`gmail/auth.py`'s `__main__` block remains available too if you'd rather run
it as a standalone script.