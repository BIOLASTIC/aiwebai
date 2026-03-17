# Gemini Unified Gateway — Configuration Guide

## 1. Overview

This gateway exposes **two upstream Gemini libraries** behind a unified REST API:

| Adapter | Library | Best for |
|---------|---------|----------|
| **webapi** | `gemini-webapi` (HanaokaYuzu) | Chat, streaming, image generation*, image editing*, gems, extensions, history |
| **mcpcli** | `gemini-web-mcp-cli` (gemcli) | Image generation (Imagen 3), video gen, music gen, deep research, usage limits |

> **\* Image generation & editing via webapi require a Gemini Advanced subscription.**
> The gateway automatically falls back to mcpcli (Imagen 3) when webapi cannot generate images.

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

### Method 3 — gemcli Login (mcpcli, for image/video/music gen)

```bash
gemcli login
```

Then go to **Accounts** → **Sync gemcli** to automatically import the logged-in account. The account's Google email will be detected and shown.

### Method 4 — API Key (mcpcli)

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

## 5. Models & Capabilities

### webapi adapter models (cookie auth)

| Model ID | Chat | Image Gen* | Image Edit* | Thinking | Streaming |
|----------|------|-----------|-------------|---------|-----------|
| `gemini-3.0-pro` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `gemini-3.0-flash` | ✅ | ✅ | ✅ | — | ✅ |
| `gemini-3.0-flash-thinking` | ✅ | — | — | ✅ | ✅ |

> **\* Requires Gemini Advanced subscription.** Without it, image generation/editing will return an error and the gateway will automatically retry via mcpcli if a gemcli account is configured.

**Legacy aliases** (automatically mapped to current models):

| Alias | Maps to |
|-------|---------|
| `gemini-2.5-pro` | `gemini-3.0-pro` |
| `gemini-2.5-flash` | `gemini-3.0-flash` |
| `gemini-2.0-flash` | `gemini-3.0-flash` |
| `gemini-2.0-flash-thinking-exp` | `gemini-3.0-flash-thinking` |
| `gemini-1.5-pro` | `gemini-3.0-pro` |
| `gemini-1.5-flash` | `gemini-3.0-flash` |

### mcpcli adapter models (gemcli login or API key)

| Model ID | Chat | Image Gen | Video Gen | Music Gen | Research |
|----------|------|-----------|-----------|-----------|---------|
| `gemini-2.0-flash` | ✅ | — | — | — | — |
| `gemini-1.5-pro` | ✅ | — | — | — | — |
| `imagen-3.0` | — | ✅ | — | — | — |
| `veo-2.0` | — | — | ✅ | — | — |
| `lyria-1.0` | — | — | — | ✅ | — |
| (any chat model) | — | — | — | — | ✅ |

---

## 6. Image Generation & Editing

### Which adapter handles images?

| Feature | Primary | Fallback | Requirement |
|---------|---------|---------|-------------|
| Generate image | mcpcli (Imagen 3) | webapi | gemcli login OR Gemini Advanced |
| Edit image | webapi | *(no fallback)* | **Gemini Advanced required** |

### Image generation flow

1. Request arrives at `POST /native/tasks/image` or `POST /v1/images/generations`
2. If `reference_file_ids` is empty → **generate mode** (mcpcli preferred → webapi fallback)
3. If `reference_file_ids` present → **edit mode** (webapi only, requires Gemini Advanced)

### Playground usage

- **Image tab** → only shows image-capable models (`gemini-3.0-pro`, `gemini-3.0-flash`, `imagen-3.0`)
- Upload a file and submit → edit mode (modifies your uploaded image)
- No file, just a prompt → generate mode (creates a new image)

### Timeouts

| Operation | Timeout | Behavior on timeout |
|-----------|---------|-------------------|
| Image generation (webapi) | 90 s | Error; retries with mcpcli |
| Image editing (webapi) | 60 s | Error with subscription hint |
| Image task (background job) | 75 s | Job marked failed |

---

## 7. API Authentication

All API requests need one of:

**Dashboard / admin routes** — JWT Bearer token:
```
Authorization: Bearer <jwt_token>
```
Obtain via `POST /admin/login` with `{"email":"...","password":"..."}`.

**OpenAI-compatible routes** — API key or JWT:
```
X-API-Key: sk-<your_key>
```
or
```
Authorization: Bearer <jwt_token>
```
Create keys in **Admin** → **API Keys**.

> **Note:** `/v1/files` (file upload) now accepts both API keys and JWT Bearer tokens.

---

## 8. Feature Routing

The gateway picks the best adapter automatically:

```
Request → resolve model alias
        → check capability flags
        → filter healthy accounts
        → prefer mcpcli for: image generation (Imagen 3), video, music, research, limits
        → prefer webapi for: chat, streaming, image editing, gems, extensions, history
        → on failure: retry with other adapter
        → 502 if no adapter can handle it
```

You can force a specific adapter via the Playground's **Provider** toggle or by passing `adapter: "webapi"` / `adapter: "mcpcli"` in the request body.

---

## 9. Cookie Refresh

`gemini-webapi` refreshes cookies automatically in the background. If a cookie expires:
1. The health checker marks the account `unhealthy`
2. The gateway stops routing requests to it
3. Go to **Accounts** → re-paste fresh cookies or re-import from Chrome

---

## 10. MCP Server Integration

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

## 11. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Logs page empty | Make API calls first — logs appear after real requests |
| Analytics empty | Same — analytics are derived from logged requests |
| Validate shows unhealthy | Cookie expired. Re-paste fresh cookies |
| 503 No accounts | Add at least one account in the Accounts page |
| Models list empty | Go to Models → Refresh Models |
| 401 on all requests | Your JWT expired; log out and log back in |
| Image gen returns "subscription required" | You need Gemini Advanced OR add a gemcli account (`gemcli login` → Accounts → Sync gemcli) |
| Image editing returns "timed out" | Gemini Advanced subscription required for image editing via webapi |
| gemcli account not showing | Run `gemcli login` in terminal, then Accounts → Sync gemcli |
| New image generated instead of editing | Ensure a reference file is uploaded in the Playground before submitting |
