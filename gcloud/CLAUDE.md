# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A FastAPI service that receives Gmail push notifications (via Google Cloud Pub/Sub), fetches new inbox messages via the Gmail API, classifies them with a local LLM (gemma4:e4b via Ollama), and auto-triages them: mail the LLM flags for deletion is confirmed via a Telegram bot before being trashed, and confirmed sender+category decisions are remembered in Redis so similar future mail is handled automatically without asking again. A daily digest of the day's actions is pushed to Telegram.

## Commands

- Install deps: `uv sync`
- Run the API server: `uv run uvicorn api:app --host 0.0.0.0 --port 8006 --reload`
- Run the one-off auth/watch script: `uv run python gmail/auth.py`
- Run tests: `uv run pytest`

There is no linter or formatter configured in this repo. `tests/test_api.py` covers the `/webhook` endpoint with FastAPI's `TestClient`, mocking `fetch_mails` and `mail_triage.process_new_mails` so it runs without live Gmail/Ollama/Redis/Telegram — no external services needed.

## Architecture

Source is organized by domain into subpackages; `api.py`, `config.py`, `models.py`, and `exceptions.py` stay at the project root since they're cross-cutting. All modules import each other with absolute imports (e.g. `from gmail.auth import ...`, `from triage import memory_store`) — this works because `uv run uvicorn api:app` is always run from the project root, which Python/uvicorn puts on `sys.path`.

- **`gmail/auth.py`** (was `gmail_auth.py`) — Core Gmail integration module, imported by `api.py` and `triage/mail_triage.py`.
  - `get_credentials()` loads OAuth2 credentials from `token.json`, refreshing the token if expired. Raises `InvalidCredentials` (from `exceptions.py`) if `token.json` is missing.
  - `_complete_oauth_workflow()` / `__main__` block — one-time interactive OAuth setup: opens a browser via `InstalledAppFlow.from_client_secrets_file("credentials.json", ...)` and writes `token.json`. Run this script directly (not through the API) whenever `token.json` needs to be (re)created.
  - `renew_watch()` calls Gmail's `users().watch()` to register the INBOX for push notifications against the Pub/Sub topic `TOPIC_NAME` (`projects/trocks-ai-gmail/topics/trocks-ai-gmail-topic`). Gmail watches expire (~7 days); returns the watch response dict on success or `None` on failure (never raises) so callers can detect and alert on failure. Scheduled automatically — see `api.py` below.
  - `fetch_mails(notification_history_id)` — called from the Gmail webhook with the `historyId` from the push notification. That value is the mailbox's *current* state, not a safe `startHistoryId` (`history.list` only returns records strictly after `startHistoryId`, so passing the notification's own id always returns empty) — so `fetch_mails` instead uses a persisted "last processed" checkpoint (`gmail:last_history_id` in Redis, via `_get_last_history_id`/`_set_last_history_id`) as `startHistoryId`, falling back to the notification's id only if no checkpoint exists yet. After a successful `history.list()` call the checkpoint advances to `response["historyId"]` (Gmail's authoritative current historyId as of that call). `renew_watch()` seeds the checkpoint from the `watch()` response the first time only (never overwrites an existing checkpoint, so a routine weekly renewal can't cause a backlog to be silently skipped). If the checkpoint is too old (Gmail 404s as invalid/expired `startHistoryId`), `fetch_mails` fast-forwards the checkpoint to the notification's id and returns no messages rather than retrying the same stale checkpoint forever — any mail in that gap is unrecoverably missed. Uses `users().history().list()` filtered server-side to `messageAdded` events still labeled `INBOX`, then fetches full message content for each via `_fetch_mail`.
  - `_fetch_mail()` extracts headers (Subject/From/Date) and body from a Gmail message payload, returning a `MailMessage` (from `models.py`). Multipart messages are handled by `_get_body()`, which prefers `text/html` (converted to markdown via `html2text`) and falls back to `text/plain`.
  - `trash_message(message_id, service=None)` — moves a message to Gmail Trash (reversible; not a permanent delete).
- **`llm/classifier.py`** (was `llm_classifier.py`) — `classify_email(mail, preferences=None)` calls a local Ollama model (`config.OLLAMA_HOST`/`OLLAMA_MODEL`, default `gemma4:e4b`) with a prompt, asking for `{category, action, reason}` JSON. `category` is drawn from a small closed vocabulary (`promotional`, `newsletter`, `security-alert`, `billing`, `transactional`, `personal`, `spam`, `other`) so it can double as a memory key; `action` is `delete` or `keep`. `transactional` is deliberately **not** a blanket "keep" category — the prompt tells the LLM some transactional mail (small amounts, specific accounts, routine confirmations) should be deleted, and if a `preferences` list (learned rule sentences, see `memory_store.get_preferences()` below) is passed in, it's appended to the prompt so the LLM applies them. `summarize_preference(sender, subject, body, category, action)` generalizes one confirmed Telegram decision into a single reusable rule sentence (free-text, not JSON) — used to grow the learned-preferences list.
- **`triage/memory_store.py`** — Redis-backed persistence (`config.REDIS_HOST/PORT/DB`).
  - Rules are keyed on **sender + category** (`rule:{sender}:{category}`), not sender alone — the same sender can have some mail auto-deleted (e.g. promos) and other mail always kept (e.g. billing statements). Not used for the `transactional` category (see `learned_preferences` below) since sender+category is too coarse when the right action depends on mail content (amount, account, alert type) rather than just who sent it.
  - `pending:{message_id}` holds a mail awaiting Telegram confirmation (TTL ~3 days), including a truncated `body` so a later confirmation can be generalized into a preference.
  - `actions:{YYYY-MM-DD}` is a list of every triage decision made that day, consumed and cleared by the daily digest job.
  - `learned_preferences` is a Redis list of free-text rule sentences (e.g. "Delete UPI alerts for account ending 934") accumulated via `add_preference`/`get_preferences`, fed into every `classify_email` call so the LLM's decisions incorporate past corrections — this is how "delete some transactional mail" nuance (amount thresholds, specific accounts, mail sub-types) is learned without hand-coded predicate logic.
- **`telegram/bot.py`** (was `telegram_bot.py`) — thin `httpx` wrapper over the Telegram Bot HTTP API: `send_confirmation` (message + inline Delete/Keep buttons), `answer_callback`, `send_message` (used for the digest).
- **`triage/mail_triage.py`** — orchestration layer tying the above together:
  - `process_new_mails(mails)` — fetches `memory_store.get_preferences()` once per batch, classifies each mail (passing those preferences in), checks for an existing sender+category rule (auto-acts if found), otherwise auto-keeps LLM-suggested "keep" mail silently or asks for confirmation via Telegram for LLM-suggested "delete" mail.
  - `handle_telegram_callback(callback_data, callback_query_id)` — resolves a Delete/Keep button press and logs the action. For `category == "transactional"`, generalizes the confirmation via `llm_classifier.summarize_preference` and appends it to `learned_preferences` instead of saving a blanket sender+category rule (which would incorrectly apply to *all* future transactional mail from that sender, e.g. large transfers as well as small alerts). For every other category, saves a sender+category rule as before.
  - `send_daily_summary()` — reads and clears today's action log, sends a digest to Telegram.
- **`api.py`** — FastAPI app exposing:
  - `GET /health` — basic health check.
  - `POST /webhook` — the Gmail Pub/Sub push subscription target. Base64-decodes `message.data` into JSON containing `emailAddress`/`historyId`, decodes it, then hands `historyId` to `BackgroundTasks` (`_fetch_and_triage`, which calls `gmail.auth.fetch_mails` then `triage.mail_triage.process_new_mails`) so the response returns immediately rather than blocking on Gmail/LLM/Telegram round-trips — needed to stay under the Pub/Sub push ack deadline.
  - `POST /telegram-webhook` — the Telegram bot's webhook target; forwards `callback_query` updates (Delete/Keep button presses) to `triage.mail_triage.handle_telegram_callback`.
  - `POST /gmail/renew-watch` — on-demand trigger for `gmail.auth.renew_watch()`, for manually forcing a renewal outside the weekly schedule. Returns `{status, historyId, expiration}` on success or `502` on failure (does not send a Telegram alert — the caller already gets the failure directly in the response, unlike the scheduled job below).
  - An APScheduler `BackgroundScheduler`, started via the app's `lifespan`, runs two cron jobs: `triage.mail_triage.send_daily_summary` daily at `config.DAILY_SUMMARY_TIME`, and `_renew_gmail_watch` (wraps `gmail.auth.renew_watch`) weekly at `config.GMAIL_WATCH_RENEWAL_DAY`/`GMAIL_WATCH_RENEWAL_TIME` (default Saturday 11:00) — well within the ~7-day expiry window, so a missed run is harmless. `_renew_gmail_watch` sends a Telegram alert if renewal fails (`renew_watch` returning `None`), since a lapsed watch means new mail silently stops triggering `/webhook`.
- **`config.py`** — all environment-driven settings (Ollama, Redis, Telegram, digest time), loaded via `python-dotenv` from a local `.env`.
- **`models.py`** — `MailMessage` pydantic model (message_id, subject, sender, body, received_on).
- **`scripts/create_pubsub_watch.py`** (was `main.py`) — standalone script for one-off Pub/Sub topic creation + Gmail `watch()` registration (duplicates logic also present in `gmail/auth.py`); not imported by the API.
- **`exceptions.py`** — defines `InvalidCredentials`.

## Setup dependencies (see README.md for full walkthrough)

This service depends on external configuration that isn't part of the code:
1. A GCP project (`trocks-ai-gmail`) with the Gmail API and Pub/Sub API enabled.
2. A Pub/Sub topic (`trocks-ai-gmail-topic`) with Gmail granted publish rights.
3. A push subscription pointing at a publicly reachable HTTPS URL for `POST /webhook` (a tunnel like zrok is used for local dev).
4. OAuth setup: `credentials.json` (OAuth client secrets) is used once by `gmail/auth.py`'s `_complete_oauth_workflow()` to produce `token.json`, which the running API then relies on via `get_credentials()`.
5. Gmail's `watch()` must be re-invoked periodically (it expires ~7 days) to keep push notifications flowing — handled automatically by the weekly `_renew_gmail_watch` job in `api.py` once the service is running (default Saturday 11:00); `POST /gmail/renew-watch` can also trigger it on demand, and `gmail/auth.py`'s `__main__` block can be run manually if needed.
6. A local Ollama server with `gemma4:e4b` pulled (`ollama pull gemma4:e4b`), reachable at `OLLAMA_HOST`.
7. A running Redis instance, reachable at `REDIS_HOST`/`REDIS_PORT`.
8. A Telegram bot (`TELEGRAM_BOT_TOKEN`) with its webhook registered once against the same public tunnel: `https://api.telegram.org/bot<TOKEN>/setWebhook?url=<PUBLIC_URL>/telegram-webhook`. `TELEGRAM_CHAT_ID` is the chat the bot sends confirmations/digests to.
9. A `.env` file (gitignored) supplying the env vars consumed by `config.py`.

`credentials.json`, `token.json`, and `.env` are gitignored — never commit them.

## Notes

- Logging is configured identically (and independently) in `gmail/auth.py` and `api.py` — INFO level, stream handler, format includes filename/line/thread.
- `gmail/`, `llm/`, `telegram/`, and `triage/` are local subpackages, not third-party ones — `telegram/` in particular would shadow the `python-telegram-bot` package's `telegram` module if that were ever added as a dependency (it currently isn't; this project talks to the Telegram Bot API directly via `httpx`).
- `SCOPES = ["https://mail.google.com/"]` grants full Gmail access (not read-only).
- Deletion always goes through `trash_message` (Gmail Trash), never a permanent delete — the LLM/Telegram pipeline can misfire, and trash is recoverable.
- Category labels come from an LLM call per message, not a fixed taxonomy enforced by code — labeling can drift, which would fragment memory rules for what a human would consider "the same kind of mail" from a sender.
- **Known gap (TODO):** `fetch_mails` doesn't page through `history.list`'s `nextPageToken` — a notification batch large enough to span multiple pages would silently lose the entries on later pages.
