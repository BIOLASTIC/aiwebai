# Gemini Unified Gateway — Configuration Guide

## 1. Overview

This gateway exposes **two upstream Gemini libraries** behind a unified REST API:

| Adapter | Library | Best for |
|---------|---------|----------|
| **webapi** | `gemini-webapi` (HanaokaYuzu) | Chat, streaming, image gen, gems, extensions, history |
| **mcpcli** | `gemini-web-mcp-cli` | Video gen, music gen, deep research, usage limits |

---

## 2. Quick Start

```bash
# 1. Clone / enter project
cd gemini-unified-gateway

# 2. Backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Database
python -m backend.app.db.seed   # creates admin user

# 4. Run backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 6400 --reload

# 5. Frontend
cd frontend && npm install && npm run dev
```

Open: http://localhost:6401
API docs: http://localhost:6400/docs
Default login: admin@local / admin123 (change immediately)

---

## 3. Adding a Gemini Account

### Method 1 — Browser Cookie (webapi, recommended)

1. Login to https://gemini.google.com in Chrome
2. Open DevTools → Application → Cookies → https://gemini.google.com
3. Copy values for:
   - `__Secure-1PSID`
   - `__Secure-1PSIDTS`
4. In the dashboard → **Accounts** → **Add Manual**
5. Provider: `WebApi (Browser Cookies)`
6. Credentials: `<PSID value>|<PSIDTS value>` (pipe-separated)

### Method 2 — Chrome Import (same machine only)

Click **Import Chrome** on the Accounts page. Requires you to be logged into Gemini in Chrome on the same machine as the server.

### Method 3 — API Key (mcpcli)

1. Get a key from https://aistudio.google.com/apikey
2. Add account → Provider: `MCP-CLI`
3. Credentials: your API key

---

## 4. Environment Variables (.env)

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | 64-char random string for JWT signing |
| `MASTER_ENCRYPTION_KEY` | Yes | Fernet key for encrypting stored cookies |
| `GEMINI_COOKIE_1PSID` | Optional | Quick-start cookie (no account needed in DB) |
| `GEMINI_COOKIE_1PSIDTS` | Optional | Pair with above |
| `DATABASE_URL` | Yes | SQLite default: `sqlite+aiosqlite:///./gemini_gateway.db` |
| `CORS_ORIGINS` | Yes | Frontend origin, e.g. `["http://localhost:6401"]` |

Generate keys:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 5. Models Reference

### webapi adapter models (cookie auth)

| Model ID | Notes |
|----------|-------|
| `gemini-2.5-pro` | Best reasoning |
| `gemini-2.5-flash` | Fast + capable |
| `gemini-2.0-flash` | Fast, good default |
| `gemini-2.0-flash-thinking-exp` | Chain-of-thought visible |
| `gemini-1.5-pro` | Stable, 1M context |
| `gemini-1.5-flash` | Fast, 1M context |
| `gemini-1.5-flash-8b` | Lightweight |
| `learnlm-1.5-pro-experimental` | Educational tuning |

### mcpcli adapter models (API key or profile)

| Model ID | Use case |
|----------|----------|
| `gemini-2.0-flash` | Chat |
| `gemini-1.5-pro` | Chat |
| `imagen-3.0` | Image generation |
| `veo-2.0` | Video generation |
| `lyria-1.0` | Music generation |

### Aliases

| Alias | Resolves to |
|-------|-------------|
| `gemini-flash-latest` | `gemini-2.0-flash` |
| `gemini-pro-latest` | `gemini-1.5-pro` |
| `gemini-thinking-latest` | `gemini-2.0-flash-thinking-exp` |
| `gemini-video-latest` | `veo-2.0` |
| `gemini-music-latest` | `lyria-1.0` |

Refresh the model list: **Models** page → **Refresh Models**, or `POST /admin/models/refresh`.

---

## 6. API Authentication

All API requests need one of:

**Dashboard / admin routes** — JWT Bearer token:
```
Authorization: Bearer <jwt_token>
```
Obtain via `POST /admin/login` with `{"email":"...","password":"..."}`.

**OpenAI-compatible routes** — API key:
```
X-API-Key: sk-<your_key>
```
Create keys in **Admin** → **API Keys**.

---

## 7. Feature Routing

The gateway picks the best adapter automatically:

```
Request → resolve model alias
        → check capability flags
        → filter healthy accounts
        → prefer webapi for: chat, streaming, image_edit, gems, extensions, history
        → prefer mcpcli for: video, music, research, limits
        → on failure: retry with other adapter
        → 503 if no adapter can handle it
```

You can force a specific adapter via the Playground's **Provider** toggle.

---

## 8. Cookie Refresh

`gemini-webapi` refreshes cookies automatically in the background. If a cookie expires:
1. The health checker marks the account `unhealthy`
2. The gateway stops routing requests to it
3. Go to **Accounts** → re-paste fresh cookies or re-import from Chrome

---

## 9. MCP Server Integration

The gateway exposes all features as MCP tools on port 6403.

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "gemini-gateway": {
      "url": "http://localhost:6403/mcp/sse",
      "env": { "GATEWAY_API_KEY": "sk-your-key" }
    }
  }
}
```

**Claude Code**:
```bash
claude mcp add gemini-gateway --url http://localhost:6403/mcp/sse
```

---

## 10. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Logs page empty | Make API calls first — logs appear after real requests |
| Analytics empty | Same — analytics are derived from logged requests |
| Validate shows unhealthy | Cookie expired. Re-paste fresh cookies |
| 503 No accounts | Add at least one account in the Accounts page |
| Models list empty | Go to Models → Refresh Models |
| 401 on all requests | Your JWT expired; log out and log back in |
