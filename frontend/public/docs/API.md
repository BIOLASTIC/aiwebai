# Gemini Unified Gateway — API Reference

Base URL: `http://0.0.0.0:6400`
Interactive docs: `/docs` (Swagger) · `/redoc` (ReDoc)

---

## Authentication

### Admin JWT (dashboard)
```
POST /admin/login
Content-Type: application/json

{"email": "admin@local", "password": "admin123"}
```
Returns `{"access_token": "...", "token_type": "bearer"}`.
Use as: `Authorization: Bearer <token>`

### Consumer API Key (OpenAI-compatible clients)
Create in Admin → API Keys. Use as: `X-API-Key: sk-...`

> Both API Key and JWT Bearer are accepted on `/v1/*` endpoints (including `/v1/files`).

---

## Model Capabilities Quick Reference

| Model | Chat | Image Gen | Image Edit | Thinking | Streaming | Adapter |
|-------|------|-----------|------------|---------|-----------|---------|
| `gemini-3.0-pro` | ✅ | ✅* | ✅* | ✅ | ✅ | webapi |
| `gemini-3.0-flash` | ✅ | ✅* | ✅* | — | ✅ | webapi |
| `gemini-3.0-flash-thinking` | ✅ | — | — | ✅ | ✅ | webapi |
| `imagen-3.0` | — | ✅ | — | — | — | mcpcli |
| `veo-2.0` | — | — | ✅ (video) | — | — | mcpcli |
| `lyria-1.0` | — | — | ✅ (music) | — | — | mcpcli |

> **\* Requires Gemini Advanced subscription.** The gateway auto-falls back to `imagen-3.0` (mcpcli) for image generation when webapi fails.

**Legacy model aliases** (all still work):
`gemini-2.5-pro` → `gemini-3.0-pro` · `gemini-2.0-flash` → `gemini-3.0-flash` · `gemini-1.5-pro` → `gemini-3.0-pro`

---

## OpenAI-Compatible Endpoints

### List Models
```
GET /v1/models
Authorization: Bearer <token>  OR  X-API-Key: sk-...
```
Returns all available models with `capabilities` field showing what each model supports.

### Chat Completion
```
POST /v1/chat/completions
X-API-Key: sk-...

{
  "model": "gemini-3.0-flash",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}
```

**Streaming** — set `"stream": true`, response is SSE:
```
data: {"id":"chatcmpl-...","choices":[{"delta":{"content":"Hello"},"index":0}]}
data: {"id":"chatcmpl-...","choices":[{"delta":{},"finish_reason":"stop","index":0}]}
data: [DONE]
```

### Image Generation
```
POST /v1/images/generations
X-API-Key: sk-...

{
  "prompt": "A futuristic cityscape at sunset",
  "n": 1
}
```

**Routing:** Prefers mcpcli (Imagen 3) → falls back to webapi (requires Gemini Advanced).

### Image Editing
```
POST /v1/images/edits
X-API-Key: sk-...
Content-Type: multipart/form-data

image=<file>
prompt="Make it black and white"
```

**Routing:** Always uses webapi. Requires **Gemini Advanced subscription**. Times out after 60 s.

### File Upload
```
POST /v1/files
Authorization: Bearer <token>  OR  X-API-Key: sk-...
Content-Type: multipart/form-data

file=<your_file>
```
Returns `{"id": "file_abc123", "filename": "...", "size": ...}`.

Use the returned `id` as a `reference_file_ids` entry in native task requests.

---

## Native Gemini Endpoints

### Image Generation (async job)
```
POST /native/tasks/image
X-API-Key: sk-...

{
  "prompt": "A red sports car in a city at night",
  "model": "imagen-3.0",
  "account_id": 1
}
```
Returns `{"job_id": 5, "status": "pending"}`

**Image Editing** — include `reference_file_ids`:
```json
{
  "prompt": "Make it black and white",
  "reference_file_ids": ["file_abc123"],
  "account_id": 1
}
```
> When `reference_file_ids` is provided, the gateway calls the image **edit** endpoint (webapi, requires Gemini Advanced). Without it, standard image generation is used.

### Video Generation (async job)
```
POST /native/tasks/video
X-API-Key: sk-...

{"prompt": "A cat playing piano in a jazz club", "model": "veo-2.0"}
```
Returns `{"job_id": "...", "status": "pending"}`

Poll: `GET /native/tasks/<job_id>`

### Music Generation (async job)
```
POST /native/tasks/music
X-API-Key: sk-...

{"prompt": "Upbeat electronic track with piano"}
```

### Deep Research (async job)
```
POST /native/tasks/research
X-API-Key: sk-...

{"prompt": "What are the latest advancements in quantum computing?"}
```

### Job Status
```
GET /native/tasks/{job_id}
X-API-Key: sk-...
```
Returns:
```json
{
  "job_id": 5,
  "type": "image",
  "status": "completed",
  "progress": 1.0,
  "result_url": "/uploads/gen_abc123.png",
  "error": null,
  "metadata": {
    "account": "My Account",
    "created_at": "2026-03-18T10:00:00"
  }
}
```

Job statuses: `pending` → `processing` → `completed` | `failed`

### Usage Limits
```
GET /native/limits
X-API-Key: sk-...
```

### Gems (system prompts)
```
GET    /native/gems
POST   /native/gems          {"name": "Code Reviewer", "system_prompt": "..."}
PUT    /native/gems/{id}
DELETE /native/gems/{id}
```

### Extensions
```
POST /native/extensions/run
{"extension": "youtube", "query": "best Python tutorials 2025"}
```

### Conversation History
```
GET    /native/history
DELETE /native/history/{chat_id}
```

### Temporary Chat (no history)
```
POST /native/temporary-chat
{"message": "What is 2+2?", "model": "gemini-3.0-flash"}
```

---

## Admin Endpoints

### Accounts
```
GET    /admin/accounts/              # List all accounts (includes email field)
POST   /admin/accounts/              # Add account
PATCH  /admin/accounts/{id}          # Rename / update
DELETE /admin/accounts/{id}          # Remove
POST   /admin/accounts/{id}/validate # Test health
POST   /admin/accounts/import/browser?browser=chrome
GET    /admin/accounts/gemcli-status # Check if gemcli is logged in
POST   /admin/accounts/import/gemcli # Import gemcli account (email auto-detected)
```

**Add account body:**
```json
{
  "label": "My Account",
  "provider": "webapi",
  "auth_methods": [
    {
      "auth_type": "cookie",
      "credentials": "1PSID_VALUE|1PSIDTS_VALUE"
    }
  ]
}
```

**Account response includes:**
```json
{
  "id": 1,
  "label": "My Account",
  "email": "user@gmail.com",
  "provider": "webapi",
  "is_active": true,
  "is_healthy": true
}
```

### Models
```
GET  /admin/models/          # List all models with capabilities
POST /admin/models/refresh   # Re-discover from adapters
```

Model response includes `capabilities` object:
```json
{
  "id": "gemini-3.0-pro",
  "display_name": "Gemini 3.0 Pro",
  "capabilities": {
    "chat": true,
    "images": true,
    "image_edit": true,
    "thinking": true,
    "streaming": true
  }
}
```

### Logs
```
GET /admin/logs/?page=1&page_size=50   # Paginated request logs
GET /admin/logs/{id}                   # Single log detail
```
Filter params: `endpoint`, `status_code`

### Analytics
```
GET /admin/analytics/summary   # Volume, latency, error rate, breakdowns
GET /admin/analytics/recent    # Last 10 requests
```

### API Keys
```
GET    /admin/api-keys/         # List consumer API keys
POST   /admin/api-keys/         # Create key
DELETE /admin/api-keys/{id}     # Revoke key
```

### Users
```
GET    /admin/users/
POST   /admin/users/
PATCH  /admin/users/{id}
DELETE /admin/users/{id}
```

Roles: `admin`, `operator`, `viewer`, `developer`

---

## Health Endpoints
```
GET /health   # Liveness
GET /ready    # Readiness
```

---

## Error Responses

All errors follow:
```json
{"detail": "Human-readable error message"}
```

| Code | Meaning |
|------|---------|
| 401 | Missing/invalid API key or JWT |
| 403 | Insufficient role |
| 404 | Resource not found |
| 422 | Validation error (check request body) |
| 502 | No adapter could complete the request (check account health) |
| 503 | No healthy Gemini accounts available |

---

## Example: Using with OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:6400/v1",
    api_key="sk-your-gateway-key",
)

response = client.chat.completions.create(
    model="gemini-3.0-flash",
    messages=[{"role": "user", "content": "Explain quantum entanglement simply"}],
)
print(response.choices[0].message.content)
```

## Example: Streaming with Python

```python
stream = client.chat.completions.create(
    model="gemini-3.0-pro",
    messages=[{"role": "user", "content": "Write a haiku about coding"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

## Example: Generate Image (cURL)

```bash
# Trigger async image job
curl -X POST http://localhost:6400/native/tasks/image \
  -H "X-API-Key: sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A sunset over mountains, photorealistic", "model":"imagen-3.0"}'

# Check job status
curl http://localhost:6400/native/tasks/5 \
  -H "X-API-Key: sk-your-key"
```

## Example: Image Editing (cURL)

```bash
# 1. Upload reference image
curl -X POST http://localhost:6400/v1/files \
  -H "X-API-Key: sk-your-key" \
  -F "file=@/path/to/photo.jpg"
# Returns: {"id": "file_abc123", ...}

# 2. Create edit job using the file ID
curl -X POST http://localhost:6400/native/tasks/image \
  -H "X-API-Key: sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Make it black and white", "reference_file_ids":["file_abc123"]}'
```

## Example: Video Generation (cURL)

```bash
# Video generation (returns job_id)
curl -X POST http://localhost:6400/native/tasks/video \
  -H "X-API-Key: sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A sunset time-lapse over mountains", "model":"veo-2.0"}'
```
