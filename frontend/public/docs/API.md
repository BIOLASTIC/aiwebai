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

---

## OpenAI-Compatible Endpoints

### List Models
```
GET /v1/models
Authorization: Bearer <token>  OR  X-API-Key: sk-...
```
Returns all available models with capability flags.

### Chat Completion
```
POST /v1/chat/completions
X-API-Key: sk-...

{
  "model": "gemini-2.0-flash",
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

### Image Editing
```
POST /v1/images/edits
X-API-Key: sk-...
Content-Type: multipart/form-data

image=<file>
prompt="Add a sunset sky"
```

---

## Native Gemini Endpoints

### Video Generation (async job)
```
POST /native/tasks/video
X-API-Key: sk-...

{"prompt": "A cat playing piano in a jazz club"}
```
Returns `{"job_id": "...", "status": "pending"}`

Poll: `GET /native/tasks/<job_id>`
Stream events: `GET /native/jobs/<job_id>/events` (SSE)

### Music Generation (async job)
```
POST /native/tasks/music
{"prompt": "Upbeat electronic track with piano"}
```

### Deep Research (async job)
```
POST /native/tasks/research
{"prompt": "What are the latest advancements in quantum computing?"}
```

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
{"message": "What is 2+2?", "model": "gemini-2.0-flash"}
```

---

## Admin Endpoints

### Accounts
```
GET    /admin/accounts/              # List all accounts
POST   /admin/accounts/              # Add account
PATCH  /admin/accounts/{id}          # Rename / update
DELETE /admin/accounts/{id}          # Remove
POST   /admin/accounts/{id}/validate # Test health
POST   /admin/accounts/import/browser?browser=chrome
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

### Models
```
GET  /admin/models/          # List all models in registry
POST /admin/models/refresh   # Re-discover from adapters
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
    model="gemini-2.0-flash",
    messages=[{"role": "user", "content": "Explain quantum entanglement simply"}],
)
print(response.choices[0].message.content)
```

## Example: Streaming with Python

```python
stream = client.chat.completions.create(
    model="gemini-2.5-pro",
    messages=[{"role": "user", "content": "Write a haiku about coding"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

## Example: cURL

```bash
# Chat
curl -X POST http://localhost:6400/v1/chat/completions \
  -H "X-API-Key: sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-2.0-flash","messages":[{"role":"user","content":"Hello"}]}'

# Video generation (returns job_id)
curl -X POST http://localhost:6400/native/tasks/video \
  -H "X-API-Key: sk-your-key" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A sunset time-lapse over mountains"}'
```
