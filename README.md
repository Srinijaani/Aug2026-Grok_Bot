# Aug2026-Grok_Bot

A minimal, self-contained chatbot web app powered by the [xAI Grok API](https://docs.x.ai).
It ships with an offline **demo mode** so the full chat flow works even without an API key.

## Features

- Clean, responsive chat UI (vanilla HTML/CSS/JS — no build step)
- Express backend that proxies to the OpenAI-compatible Grok Chat Completions endpoint
- Stateless conversation handling (full history resent per request)
- Offline **demo mode** when `XAI_API_KEY` is not set, so it's always runnable
- Health endpoint that reports whether a live key is configured

## Requirements

- Node.js 20+ (developed on Node 22)

## Getting started

```bash
npm install
npm start
```

Then open http://localhost:3000.

To talk to the real Grok model, copy `.env.example` to `.env` and set your key:

```bash
cp .env.example .env
# edit .env and set XAI_API_KEY=...
npm start
```

For local development with auto-reload:

```bash
npm run dev
```

## Configuration

| Variable             | Default                    | Description                                         |
| -------------------- | -------------------------- | --------------------------------------------------- |
| `XAI_API_KEY`        | _(unset → demo mode)_      | xAI API key from https://console.x.ai               |
| `GROK_MODEL`         | `grok-4`                   | Model name to use                                   |
| `XAI_API_BASE`       | `https://api.x.ai/v1`      | API base URL                                        |
| `GROK_SYSTEM_PROMPT` | _(built-in Grok persona)_  | System prompt prepended to each conversation        |
| `PORT`               | `3000`                     | Port the server listens on                          |

## API

- `GET /api/health` → `{ status, configured, mode, model }`
- `POST /api/chat` → body `{ messages: [{ role, content }, ...] }` or `{ message: "..." }`;
  returns `{ reply, model, demo }`

Example:

```bash
curl -s http://localhost:3000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello!"}'
```

## Tests

```bash
npm test
```

## Project layout

```
server.js            Express app + routes
src/grokClient.js    Grok API client with offline demo fallback
public/              Static chat UI (index.html, styles.css, app.js)
test/                Node built-in test runner tests
.cursor/             Cloud Agent environment configuration
```
