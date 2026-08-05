# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

## What this is

"Trocks AI Chatbots" — a Next.js frontend/BFF that hosts multiple AI chatbot clients (Calendar AI, Poker AI, Recipe AI) behind a shared login/dashboard shell. This app has no database or business logic of its own: it authenticates users (custom email/password backend + Google OAuth), proxies chat messages to backend agent APIs, and renders the chat UI. All real work (agent logic, persistence) lives in separate backend services referenced via env vars.

## Commands

```bash
npm run dev      # start dev server (Turbopack) at localhost:3000
npm run build    # production build (output: "standalone" per next.config.ts)
npm run start    # run the production build
npm run lint     # eslint (flat config: eslint-config-next core-web-vitals + typescript)
```

There is no test suite configured in this repo.

## Next.js version warning

This project runs **Next.js 16.2.6**, which has breaking changes vs. the Next.js you were trained on. Before making routing/middleware/data-fetching changes, check `node_modules/next/dist/docs/` (App Router docs under `01-app/`). The one that already bit this codebase's structure:

- **`middleware.ts` is now `proxy.ts`.** The middleware convention was renamed to Proxy in Next 16 — same behavior, new filename/export. This repo's `src/proxy.ts` (not `middleware.ts`) is where route-protection logic lives, exporting a `proxy` function and a `config.matcher`. Don't recreate a `middleware.ts` file expecting it to be picked up.

## Architecture

**Routing**: App Router under `src/app`. Two route groups:
- `/` — public login page (`src/app/page.tsx` + `src/components/LoginForm.tsx`)
- `/dashboard/*` — protected area (`src/app/dashboard/layout.tsx` renders a collapsible `Sidebar` built from the `NEXT_PUBLIC_CHATBOTS` env var, one page per bot: `calendarai/`, `pokerai/`, `recipeai/`)

**Auth (two independent schemes, both cookie-based via `src/lib/cookie.ts`)**:
1. Custom email/password — `POST /api/auth/custom/login` (catch-all `[[...slug]]` route) forwards credentials to `API_BASE_URL/login`, stores the response's `x-amzn-remapped-authorization` header as an httpOnly `authToken` cookie. Duplicated (near-identically) in `src/app/api/login/route.ts`, which appears to be legacy/dead code left alongside the newer catch-all route — check before extending either.
2. Google OAuth — `src/app/api/auth/google/[[...slug]]/route.ts` handles `login` (redirect to Google) and `callback` (exchange code, fetch userinfo, set `googleAccessToken`/`googleUserEmail`/`googleUserName` cookies — names centralized in `src/lib/constants.ts`), then POSTs credentials to the backend via `src/app/services/auth.ts`. Token refresh flow is `src/app/api/auth/refresh/route.ts`, which pulls the refresh token from the backend by email and calls `refreshAccessToken` in `src/lib/googleAuth.ts`.

`src/proxy.ts` gates `/dashboard/:path*`: redirects to `/` if neither `authToken` nor `googleAccessToken` cookies are present, or to `/api/auth/refresh?returnTo=<url>` if the Google access token has expired (checked live against Google's `tokeninfo` endpoint on every protected request).

**Chat flow**: All chatbot pages are client components (`"use client"`) that render the shared `src/components/ChatBot.tsx` and pass it a `sendFunc`. `sendFunc` POSTs to `/api/chat/<agent>` (catch-all route `src/app/api/chat/[[...slug]]/route.ts`), which dispatches by the `agent` slug (`calendarai` → `chatWithAI`, `pokerai` → `chatWithManagerAI`, both in `src/app/services/chat.ts`) to different backend base URLs (`API_BASE_URL` vs `MANAGER_API_BASE_URL`), attaching the user's email from the `googleUserEmail` cookie and an `x-api-key` header. `recipeai` currently has no backend wired up — it echoes a hardcoded response client-side. Conversation history/threads (`ConversationThread` in `src/lib/models.ts`) are UI-only placeholders (`TODO` in each page) — not persisted or loaded from a backend yet.

**Env vars** (see `.env`, not committed): `GOOGLE_CLIENT_ID`/`SECRET`/`REDIRECT_URI`/`AUTH_SCOPE` for OAuth; `API_BASE_URL`/`API_KEY` for the primary backend (auth + calendar agent); `MANAGER_API_BASE_URL`/`MANAGER_API_KEY` for the poker "manager" agent; `NEXT_PUBLIC_CHATBOTS` (comma-separated list, exposed client-side) drives the sidebar links — each entry is slugified (`lowercase`, spaces → `-`) to build its `/dashboard/<slug>` route, so it must match an actual page folder under `src/app/dashboard/`.

**Logging**: `src/lib/logger.tsx` — server-only structured `log(level, message, meta)`, no-ops on the client (checks `globalThis.window`).

**Deployment**: Multi-stage `Dockerfile` builds with `output: "standalone"` and runs as a non-root `nextjs` user on port 3000.
