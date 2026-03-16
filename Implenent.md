# Gemini Unified Gateway — Definitive Project Blueprint

**Project name:** `gemini-unified-gateway`
**Python:** 3.11+
**Host:** `0.0.0.0` (all interfaces)
**Port range:** `6400–6410`
**Status:** Planning phase — zero code written yet

---

## 0. Design philosophy

This gateway wraps two reverse-engineered upstream libraries behind a stable, production-quality API surface. Both upstreams can break without notice when Google changes internal web behavior. The architecture must absorb that instability and expose a calm, consistent interface.

**Core principles:**

- Adapter isolation: never merge upstream codebases; wrap them behind a shared interface
- Capability-first routing: never assume every account can do every feature
- OpenAI-compatible where possible, native Gemini endpoints where necessary
- Separate user auth from Gemini account auth — they are different systems
- Encrypt all cookie material at rest with a master key
- Redact sensitive prompt data by default in logs
- Feature parity is a living dashboard, not a one-time claim
- Graceful degradation: when one adapter breaks, fallback to the other

---

## 1. Upstream library inventory

### Adapter A — gemini-webapi (HanaokaYuzu)

| Feature | Notes |
|---------|-------|
| Text generation | Any Gemini model |
| File upload with prompts | Images, documents |
| Multi-turn chat | With metadata persistence |
| Conversation history CRUD | Read, delete |
| Temporary mode | No history saved |
| Streaming | Async generator, token-by-token |
| Model selection | Including custom model strings |
| System prompts via Gems | Apply and switch |
| Custom Gems CRUD | Create, update, delete |
| Thought/reasoning retrieval | Chain-of-thought access |
| Image generation and editing | Via Gemini's internal image tools |
| Extensions | Maps, YouTube, Flights, Hotels, Workspace |
| Reply candidate switching | View and select alternative responses |
| Cookie auth | __Secure-1PSID + __Secure-1PSIDTS |
| Auto cookie refresh | Background token refresh |
| browser-cookie3 import | Auto-import from local browser |
| Docker cookie persistence | Volume-based |
| Configurable logging | Via loguru |
| Python requirement | 3.10+ |

### Adapter B — gemini-web-mcp-cli

| Feature | Notes |
|---------|-------|
| Chat with model selection | Via web UI reverse-engineering |
| File uploads | Images, documents |
| Image generation | Text-to-image |
| Video generation | Async, requires polling |
| Music generation | Async, requires polling |
| Deep Research | Long-running research sessions |
| Usage limit checks | Query remaining quotas |
| Gems support | System prompts |
| Multi-profile support | Multiple Google accounts |
| MCP server (built-in) | SSE + STDIO transports |
| Anthropic-compatible local API | Built-in REST endpoint |
| Chrome/BotGuard support | Some features require headless Chrome |
| Automated Chrome login | Browser-based auth flow |
| Manual cookie paste | Direct cookie entry |
| Python requirement | 3.11+ |
| Status | Alpha — explicit risk warnings |

### Feature overlap and gaps

| Feature | webapi | mcp-cli | Gateway strategy |
|---------|--------|---------|-----------------|
| Chat | yes | yes | Both, prefer webapi for streaming |
| Streaming | native async | limited | webapi primary |
| Image gen | yes | yes | Both, capability-route |
| Image edit | yes | no | webapi only |
| Video gen | no | yes | mcp-cli only |
| Music gen | no | yes | mcp-cli only |
| Deep Research | no | yes | mcp-cli only |
| Extensions | yes | no | webapi only |
| Gems | yes | yes | Both, prefer webapi (full CRUD) |
| History CRUD | yes | no | webapi only |
| Temporary mode | yes | no | webapi only |
| Reply candidates | yes | no | webapi only |
| Usage limits | no | yes | mcp-cli only |
| Multi-profile | partial | yes | mcp-cli primary |
| Cookie refresh | auto | manual | webapi primary |
| MCP server | no (we build) | built-in | Our own wrapping both |

---

## 2. Architecture — four layers

### Layer 1: Provider layer (adapters)

- `webapi_adapter` — wraps gemini-webapi via direct async library calls
- `mcpcli_adapter` — wraps gemini-web-mcp-cli via library calls where stable, subprocess where not
- Shared canonical request/response Pydantic models
- Capability flags per account, per model, per provider
- Provider health state machine: healthy → degraded → unhealthy → recovering

### Layer 2: Gateway layer (API surface)

- OpenAI-compatible REST endpoints (`/v1/...`)
- Native Gemini endpoints (`/native/...`)
- SSE streaming with OpenAI event format
- Job system for long-running tasks (video, music, research)
- Standard middleware: auth, rate limits, CORS, request logging, retries
- Swagger UI at `/docs`, ReDoc at `/redoc`

### Layer 3: Control plane

- Multi-account management with encrypted credential storage
- Profile/cookie/auth lifecycle management
- Model registry with alias resolution and auto-discovery
- Analytics collector and aggregation engine
- Admin panel (web GUI)
- CLI admin utilities via Typer
- Password reset via terminal and GUI
- RBAC: admin, operator, viewer, developer roles

### Layer 4: Integration layer

- MCP server exposing all features as tools (SSE + STDIO)
- Webhook/event dispatch for job completions and alerts
- GUI test console (playground) for every feature
- Consumer API key management for external clients

---

## 3. Tech stack decisions

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.11 | Both upstreams require 3.10+; 3.11 for union types, perf |
| API framework | FastAPI | Async native, auto Swagger, SSE support, Pydantic v2 |
| Server | Uvicorn + Gunicorn | Async ASGI with worker management |
| ORM | SQLAlchemy 2.0 async | Mature, typed, migration-ready |
| Migrations | Alembic | Industry standard |
| Primary DB | PostgreSQL | Multi-connection safe, JSON columns, full-text search |
| Cache/queue | Redis | SSE fan-out, rate limiting, session cache, job queue |
| Task queue | Celery or RQ | Video/music/research are 1-5 min jobs, need background workers |
| Schemas | Pydantic v2 | FastAPI native, strict validation |
| CLI | Typer | Modern, type-hinted, auto-help |
| Frontend | React 18 + Vite + Tailwind + shadcn/ui | Fast dev, polished components |
| Charts | ECharts or Recharts | Rich analytics visualizations |
| State mgmt | Zustand | Lightweight React store |
| Logging | structlog (JSON) | Structured, machine-parseable |
| Metrics | Prometheus client + Grafana | Ops-grade observability |
| Secrets | Fernet symmetric encryption | At-rest cookie/key encryption |
| Testing | pytest + pytest-asyncio + httpx | Async-first test suite |
| Linting | ruff | Fast, all-in-one |
| Types | mypy (strict) | Static safety |
| Container | Docker Compose | Local dev: API + frontend + Postgres + Redis + worker |

---

## 3a. Port allocation

All services bind to `0.0.0.0` (accessible from any network interface).

| Port | Service | Protocol | Notes |
|------|---------|----------|-------|
| 6400 | FastAPI backend (main API + Swagger) | HTTP | Primary gateway — all /v1, /native, /admin, /health |
| 6401 | Vite frontend dev server | HTTP | React dashboard (dev mode); Nginx in production |
| 6402 | Celery Flower | HTTP | Task queue monitoring dashboard |
| 6403 | MCP SSE transport | HTTP | Dedicated MCP server for Claude/Cursor/etc. |
| 6404 | Prometheus metrics | HTTP | /metrics endpoint for scraping |
| 6405 | Grafana | HTTP | Ops dashboards (Docker container) |
| 6406 | Redis | TCP | Cache, queue broker, SSE fan-out, rate limits |
| 6407 | PostgreSQL | TCP | Primary database |
| 6408 | WebSocket live logs | WS | Real-time log streaming to GUI |
| 6409 | Reserved | — | Future use (e.g., admin-only API, gRPC) |
| 6410 | Reserved | — | Future use (e.g., public status page) |

In production (Docker Compose), Nginx on port 6400 can reverse-proxy to both the backend and frontend, eliminating the need for separate frontend port exposure.

---

## 3b. Complete dependency manifest

### Backend — Python packages (pyproject.toml)

#### Core upstream libraries (the two adapters)

| Package | Version | Purpose |
|---------|---------|---------|
| `gemini-webapi` | `>=1.15.0` | Adapter A — reverse-engineered Gemini web app |
| `gemini-webapi[browser]` | `>=1.15.0` | Optional: auto-import cookies via browser-cookie3 |
| `gemini-web-mcp-cli` | `>=0.1.0` | Adapter B — Gemini web MCP CLI with video/music/research |

#### Web framework and server

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | `>=0.115.0` | API framework, auto Swagger/OpenAPI |
| `uvicorn[standard]` | `>=0.32.0` | ASGI server with uvloop + httptools |
| `gunicorn` | `>=22.0.0` | Process manager for production (wraps uvicorn workers) |
| `starlette` | `>=0.41.0` | Pulled by FastAPI; SSE, WebSocket, middleware |
| `sse-starlette` | `>=2.1.0` | Server-Sent Events response class for FastAPI |
| `websockets` | `>=13.0` | WebSocket support for live log streaming |
| `python-multipart` | `>=0.0.12` | File upload parsing (required by FastAPI) |

#### Database and ORM

| Package | Version | Purpose |
|---------|---------|---------|
| `sqlalchemy[asyncio]` | `>=2.0.35` | Async ORM with 2.0-style queries |
| `asyncpg` | `>=0.30.0` | Async PostgreSQL driver |
| `alembic` | `>=1.14.0` | Database migration management |
| `psycopg2-binary` | `>=2.9.9` | Sync PG driver (for Alembic migrations) |

#### Cache, queue, and background tasks

| Package | Version | Purpose |
|---------|---------|---------|
| `redis[hiredis]` | `>=5.2.0` | Async Redis client with C-accelerated parser |
| `celery[redis]` | `>=5.4.0` | Distributed task queue for long jobs |
| `flower` | `>=2.0.0` | Celery monitoring web dashboard |

#### Authentication and security

| Package | Version | Purpose |
|---------|---------|---------|
| `pyjwt[crypto]` | `>=2.9.0` | JWT creation/validation with RSA support |
| `bcrypt` | `>=4.2.0` | Password hashing |
| `cryptography` | `>=43.0.0` | Fernet symmetric encryption for stored secrets |
| `passlib[bcrypt]` | `>=1.7.4` | Password hashing utilities (wraps bcrypt) |

#### Schemas and validation

| Package | Version | Purpose |
|---------|---------|---------|
| `pydantic` | `>=2.9.0` | Data validation and schema definition |
| `pydantic-settings` | `>=2.6.0` | Settings management from env/.env files |
| `email-validator` | `>=2.2.0` | Email format validation for user accounts |

#### HTTP clients

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | `>=0.27.0` | Async HTTP client for health checks, webhooks |
| `aiofiles` | `>=24.1.0` | Async file I/O for uploads and exports |

#### Logging and observability

| Package | Version | Purpose |
|---------|---------|---------|
| `structlog` | `>=24.4.0` | Structured JSON logging |
| `loguru` | `>=0.7.2` | Also used internally by gemini-webapi |
| `prometheus-client` | `>=0.21.0` | Prometheus metrics exposition |
| `prometheus-fastapi-instrumentator` | `>=7.0.0` | Auto-instrument FastAPI routes |

#### CLI

| Package | Version | Purpose |
|---------|---------|---------|
| `typer[all]` | `>=0.12.0` | CLI framework with rich output |
| `rich` | `>=13.9.0` | Terminal formatting, tables, progress bars |
| `click` | `>=8.1.0` | Pulled by Typer; also useful for prompts |

#### MCP server

| Package | Version | Purpose |
|---------|---------|---------|
| `fastmcp` | `>=2.12.0` | Model Context Protocol server library |
| `mcp` | `>=1.0.0` | MCP SDK types and client session |

#### Rate limiting and middleware

| Package | Version | Purpose |
|---------|---------|---------|
| `slowapi` | `>=0.1.9` | Per-key/IP rate limiting via Redis backend |

#### Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| `python-dotenv` | `>=1.0.1` | .env file loading |
| `orjson` | `>=3.10.0` | Fast JSON serialization (10x faster than stdlib) |
| `tenacity` | `>=9.0.0` | Retry with exponential backoff |
| `cachetools` | `>=5.5.0` | In-memory caching (TTL, LRU) |
| `croniter` | `>=3.0.0` | Cron schedule parsing for periodic tasks |
| `python-dateutil` | `>=2.9.0` | Date/time utilities |
| `pillow` | `>=10.4.0` | Image processing for uploads and thumbnails |
| `aiohttp` | `>=3.10.0` | Alternate async HTTP (some adapters may need it) |
| `browser-cookie3` | `>=0.19.1` | Extract cookies from local browsers |

#### Celery extensions

| Package | Version | Purpose |
|---------|---------|---------|
| `celery-redbeat` | `>=2.2.0` | Redis-based periodic task scheduler (replaces celery beat + DB) |
| `celery-singleton` | `>=0.3.1` | Prevent duplicate long-running tasks |

#### Dev dependencies (pyproject.toml [dev] extras)

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | `>=8.3.0` | Test framework |
| `pytest-asyncio` | `>=0.24.0` | Async test support |
| `pytest-cov` | `>=5.0.0` | Coverage reporting |
| `pytest-xdist` | `>=3.5.0` | Parallel test execution |
| `httpx` | `>=0.27.0` | Test client (AsyncClient) |
| `factory-boy` | `>=3.3.0` | Test data factories |
| `faker` | `>=30.0.0` | Fake data generation |
| `ruff` | `>=0.7.0` | Linter + formatter (replaces flake8, black, isort) |
| `mypy` | `>=1.13.0` | Static type checker |
| `sqlalchemy[mypy]` | `>=2.0.35` | SQLAlchemy mypy plugin |
| `pre-commit` | `>=4.0.0` | Git pre-commit hooks |
| `bandit` | `>=1.7.10` | Security vulnerability scanner |
| `locust` | `>=2.31.0` | Load testing |
| `watchfiles` | `>=0.24.0` | File watcher for auto-reload (used by uvicorn) |

### Frontend — npm packages (package.json)

#### Core framework

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | `^18.3.0` | UI library |
| `react-dom` | `^18.3.0` | React DOM renderer |
| `react-router-dom` | `^6.28.0` | Client-side routing |
| `typescript` | `^5.6.0` | Type safety |

#### Build tools

| Package | Version | Purpose |
|---------|---------|---------|
| `vite` | `^5.4.0` | Build tool and dev server |
| `@vitejs/plugin-react` | `^4.3.0` | React fast refresh for Vite |
| `@types/react` | `^18.3.0` | React TypeScript types |
| `@types/react-dom` | `^18.3.0` | React DOM TypeScript types |

#### Styling and UI components

| Package | Version | Purpose |
|---------|---------|---------|
| `tailwindcss` | `^3.4.0` | Utility-first CSS framework |
| `postcss` | `^8.4.0` | CSS processing (Tailwind dependency) |
| `autoprefixer` | `^10.4.0` | Vendor prefix (Tailwind dependency) |
| `@tailwindcss/forms` | `^0.5.9` | Form element styling plugin |
| `@tailwindcss/typography` | `^0.5.15` | Prose styling plugin (for markdown render) |
| `class-variance-authority` | `^0.7.0` | Variant-based component styling (shadcn dep) |
| `clsx` | `^2.1.0` | Conditional class joining |
| `tailwind-merge` | `^2.5.0` | Merge Tailwind classes without conflicts |
| `tailwindcss-animate` | `^1.0.7` | Animation utilities (shadcn dep) |

#### shadcn/ui components (installed via CLI: `npx shadcn@latest init`)

| Component | Purpose |
|-----------|---------|
| `button` | Buttons throughout app |
| `input` | Form inputs |
| `label` | Form labels |
| `card` | Dashboard cards, account cards |
| `dialog` | Modals (add account, confirm delete) |
| `dropdown-menu` | Account switcher, model picker |
| `select` | Dropdowns |
| `tabs` | Playground feature tabs |
| `table` | Logs table, model table, user table |
| `badge` | Health status, capability flags |
| `avatar` | User avatars |
| `toast` | Notifications (via sonner) |
| `sheet` | Side panels (request detail) |
| `command` | Command palette / search |
| `separator` | Visual dividers |
| `skeleton` | Loading states |
| `switch` | Toggles (streaming, debug mode) |
| `slider` | Range controls |
| `textarea` | Prompt input, cookie paste |
| `scroll-area` | Scrollable log viewer |
| `alert` | Error/warning messages |
| `progress` | Job progress bars (video, music, research) |
| `popover` | Tooltips, info popovers |
| `form` | Form wrapper (react-hook-form integration) |
| `navigation-menu` | Sidebar navigation |
| `accordion` | Collapsible sections |
| `chart` | shadcn chart wrapper (uses Recharts internally) |
| `sonner` | Toast notification library |

#### Charts and data visualization

| Package | Version | Purpose |
|---------|---------|---------|
| `recharts` | `^2.13.0` | React-native charting (line, bar, pie, area) |
| `echarts` | `^5.5.0` | Rich charts for analytics (heatmap, gauge, treemap) |
| `echarts-for-react` | `^3.0.2` | React wrapper for ECharts |

#### State management and data fetching

| Package | Version | Purpose |
|---------|---------|---------|
| `zustand` | `^4.5.0` | Lightweight global state |
| `@tanstack/react-query` | `^5.59.0` | Server state, caching, refetch |
| `axios` | `^1.7.0` | HTTP client with interceptors |

#### Utilities

| Package | Version | Purpose |
|---------|---------|---------|
| `date-fns` | `^4.1.0` | Date formatting and manipulation |
| `lucide-react` | `^0.451.0` | Icon library (matches shadcn) |
| `react-hook-form` | `^7.53.0` | Form management |
| `@hookform/resolvers` | `^3.9.0` | Zod resolver for react-hook-form |
| `zod` | `^3.23.0` | Schema validation (frontend) |
| `react-markdown` | `^9.0.0` | Render deep research results |
| `react-syntax-highlighter` | `^15.5.0` | Code block highlighting |
| `react-resizable-panels` | `^2.1.0` | Resizable playground panels |
| `eventsource-parser` | `^3.0.0` | Parse SSE streams in browser |
| `js-cookie` | `^3.0.5` | Cookie management for auth |

#### Dev dependencies (frontend)

| Package | Version | Purpose |
|---------|---------|---------|
| `eslint` | `^9.12.0` | Linter |
| `@eslint/js` | `^9.12.0` | ESLint JS config |
| `typescript-eslint` | `^8.8.0` | TypeScript ESLint rules |
| `eslint-plugin-react-hooks` | `^5.1.0` | React hooks linting |
| `eslint-plugin-react-refresh` | `^0.4.12` | React fast refresh linting |
| `@types/js-cookie` | `^3.0.6` | Type definitions |
| `prettier` | `^3.3.0` | Code formatter |
| `prettier-plugin-tailwindcss` | `^0.6.0` | Sort Tailwind classes |

### System / infrastructure dependencies

| Component | Image / Package | Version | Port |
|-----------|----------------|---------|------|
| PostgreSQL | `postgres` | `16-alpine` | 6407 |
| Redis | `redis` | `7-alpine` | 6406 |
| Grafana | `grafana/grafana-oss` | `11-alpine` | 6405 |
| Prometheus | `prom/prometheus` | `v2.54.0` | 6404 |
| Nginx (prod) | `nginx` | `1.27-alpine` | 6400 (reverse proxy) |
| Node.js (build) | `node` | `20-alpine` | build-time only |
| Python | `python` | `3.11-slim` | runtime |

### Vite plugins (vite.config.ts)

| Plugin | Purpose |
|--------|---------|
| `@vitejs/plugin-react` | React HMR and JSX transform |
| `vite-plugin-svgr` | Import SVGs as React components |
| `vite-tsconfig-paths` | Resolve TypeScript path aliases |

### Tailwind plugins (tailwind.config.js)

| Plugin | Purpose |
|--------|---------|
| `@tailwindcss/forms` | Better default form styling |
| `@tailwindcss/typography` | Prose classes for markdown/research results |
| `tailwindcss-animate` | Animation utility classes (shadcn requirement) |

### FastAPI middleware / plugins

| Middleware | Package | Purpose |
|-----------|---------|---------|
| CORS | `fastapi.middleware.cors.CORSMiddleware` | Cross-origin for frontend |
| Trusted host | `starlette.middleware.trustedhost` | Restrict allowed hosts |
| GZip | `fastapi.middleware.gzip.GZipMiddleware` | Response compression |
| Rate limiter | `slowapi` (`>=0.1.9`) | Per-key/IP rate limiting via Redis |
| Prometheus | `prometheus-fastapi-instrumentator` | Auto-metric all routes |
| Session | `starlette.middleware.sessions` | Optional session support |
| Request ID | Custom (based on `uuid`) | Correlation ID injection |

### Celery plugins / extensions

| Plugin | Purpose |
|--------|---------|
| `celery[redis]` | Redis as broker and result backend |
| `flower` | Web monitoring UI on port 6402 |
| `celery-redbeat` (`>=2.2.0`) | Redis-based periodic task scheduler (replaces celery beat + DB) |
| `celery-singleton` (`>=0.3.1`) | Prevent duplicate long-running tasks |

### Alembic plugins

| Plugin | Purpose |
|--------|---------|
| `alembic` | Core migration tool |
| `sqlalchemy[asyncio]` | Async engine support in migration env |

### ruff configuration (pyproject.toml)

| Setting | Value | Purpose |
|---------|-------|---------|
| `target-version` | `"py311"` | Python 3.11 target |
| `line-length` | `120` | Max line width |
| `select` | `["E", "W", "F", "I", "N", "UP", "S", "B", "A", "C4", "PT", "RUF"]` | Error, warning, pyflakes, isort, naming, upgrade, bandit, bugbear, builtins, comprehensions, pytest, ruff-specific |
| `ignore` | `["E501"]` | Let line-length handle long lines |

### mypy configuration (pyproject.toml)

| Setting | Value |
|---------|-------|
| `python_version` | `"3.11"` |
| `strict` | `true` |
| `plugins` | `["pydantic.mypy", "sqlalchemy.ext.mypy.plugin"]` |
| `disallow_untyped_defs` | `true` |
| `warn_return_any` | `true` |

---

## 3c. Environment configuration (.env.example)

```bash
# =============================================================
# GEMINI UNIFIED GATEWAY — ENVIRONMENT CONFIGURATION
# =============================================================
# Copy to .env and fill in values. Never commit .env to git.
# =============================================================

# ----- Network / Ports -----
HOST=0.0.0.0
API_PORT=6400
FRONTEND_PORT=6401
FLOWER_PORT=6402
MCP_PORT=6403
PROMETHEUS_PORT=6404
GRAFANA_PORT=6405
REDIS_PORT=6406
POSTGRES_PORT=6407
WEBSOCKET_PORT=6408

# ----- Application -----
APP_NAME=gemini-unified-gateway
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=change-me-to-a-64-char-random-string
MASTER_ENCRYPTION_KEY=change-me-to-a-fernet-key

# ----- Database (PostgreSQL) -----
POSTGRES_HOST=0.0.0.0
POSTGRES_PORT=6407
POSTGRES_DB=gemini_gateway
POSTGRES_USER=gateway
POSTGRES_PASSWORD=change-me-pg-password
DATABASE_URL=postgresql+asyncpg://gateway:change-me-pg-password@0.0.0.0:6407/gemini_gateway
DATABASE_URL_SYNC=postgresql+psycopg2://gateway:change-me-pg-password@0.0.0.0:6407/gemini_gateway

# ----- Redis -----
REDIS_HOST=0.0.0.0
REDIS_PORT=6406
REDIS_PASSWORD=
REDIS_URL=redis://0.0.0.0:6406/0
CELERY_BROKER_URL=redis://0.0.0.0:6406/1
CELERY_RESULT_BACKEND=redis://0.0.0.0:6406/2

# ----- JWT Auth -----
JWT_SECRET=change-me-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=1440
JWT_REFRESH_EXPIRE_DAYS=7

# ----- Default Gemini Account (quick start) -----
# Option 1: Cookie auth (for gemini-webapi)
GEMINI_COOKIE_1PSID=
GEMINI_COOKIE_1PSIDTS=

# Option 2: API key (for CLI-backed features)
GEMINI_API_KEY=

# ----- Gemini Web MCP CLI specific -----
GEMINI_MCP_CLI_CHROME_PROFILE=
GEMINI_MCP_CLI_HEADLESS=true
GEMINI_MCP_CLI_BOTGUARD=false

# ----- Celery / Task Queue -----
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIMEOUT=600
FLOWER_BASIC_AUTH=admin:change-me-flower-password

# ----- Rate Limiting -----
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_ACCOUNT_PER_MINUTE=10
RATE_LIMIT_STORAGE_URL=redis://0.0.0.0:6406/3

# ----- Analytics -----
ANALYTICS_RETENTION_DAYS=90
ANALYTICS_AGGREGATION_INTERVAL=3600

# ----- Model Registry -----
MODEL_REFRESH_INTERVAL_HOURS=6
MODEL_PASS_THROUGH_UNKNOWN=true

# ----- MCP Server -----
MCP_ENABLED=true
MCP_HOST=0.0.0.0
MCP_PORT=6403
MCP_AUTH_REQUIRED=true

# ----- Webhooks -----
WEBHOOK_RETRY_MAX=3
WEBHOOK_RETRY_BACKOFF=30

# ----- Canary Tests -----
CANARY_ENABLED=true
CANARY_INTERVAL_SECONDS=300

# ----- Package Watcher -----
PACKAGE_WATCH_INTERVAL_HOURS=12

# ----- Prometheus -----
PROMETHEUS_ENABLED=true

# ----- Grafana -----
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=change-me-grafana-password

# ----- CORS -----
CORS_ORIGINS=["http://0.0.0.0:6401","http://localhost:6401","http://127.0.0.1:6401"]

# ----- Log Settings -----
LOG_FILE=logs/gateway.log
LOG_ROTATION=50MB
LOG_RETENTION=30
LOG_FORMAT=json
LOG_REDACT_PROMPTS=true
LOG_STORE_FULL_PAYLOADS=false

# ----- Frontend -----
VITE_API_BASE_URL=http://0.0.0.0:6400
VITE_WS_URL=ws://0.0.0.0:6408
VITE_MCP_URL=http://0.0.0.0:6403
```

---

## 3d. Dev scripts — port-aware

### dev-start.sh

```text
Behavior:
1. Create Python venv if .venv/ missing (python3.11 -m venv .venv)
2. Activate venv, pip install -e ".[dev]"
3. Install frontend deps if node_modules/ missing (npm install --prefix frontend/)
4. Start docker compose (Postgres on 6407, Redis on 6406)
5. Wait for Postgres + Redis to be ready (healthcheck loop)
6. Run alembic upgrade head
7. Seed admin user if first run (python -m cli.main admin create-user)
8. Start uvicorn on 0.0.0.0:6400 with --reload
9. Start celery worker with Redis broker
10. Start flower on 0.0.0.0:6402
11. Start MCP SSE server on 0.0.0.0:6403
12. Start frontend vite dev server on 0.0.0.0:6401
13. Start WebSocket log server on 0.0.0.0:6408
14. Print all URLs:
    - API + Swagger:  http://0.0.0.0:6400/docs
    - Frontend:       http://0.0.0.0:6401
    - Flower:         http://0.0.0.0:6402
    - MCP SSE:        http://0.0.0.0:6403
    - Prometheus:     http://0.0.0.0:6404
    - Grafana:        http://0.0.0.0:6405
    - Live logs WS:   ws://0.0.0.0:6408
15. Store all PIDs in .dev.pids
```

### dev-stop.sh

```text
Behavior:
1. Read .dev.pids, kill each process
2. Optionally stop docker compose (with --all flag)
3. Remove .dev.pids
4. Print "Stopped"
```

### dev-restart.sh

```text
Behavior:
1. Run dev-stop.sh
2. Sleep 2 seconds
3. Run dev-start.sh
```

---

## 3e. Docker Compose — port-mapped services

### docker-compose.yml (development)

```text
Services:
  postgres:
    image: postgres:16-alpine
    ports: ["6407:5432"]
    environment: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    volumes: pgdata:/var/lib/postgresql/data
    healthcheck: pg_isready

  redis:
    image: redis:7-alpine
    ports: ["6406:6379"]
    command: redis-server --appendonly yes
    volumes: redisdata:/data
    healthcheck: redis-cli ping

  backend:
    build: docker/Dockerfile.backend
    ports: ["6400:6400"]
    command: uvicorn app.main:app --host 0.0.0.0 --port 6400 --reload
    depends_on: [postgres, redis]
    env_file: .env
    volumes: ["./backend:/app"]

  worker:
    build: docker/Dockerfile.backend
    command: celery -A app.workers worker --loglevel=info --concurrency=4
    depends_on: [postgres, redis]
    env_file: .env

  flower:
    build: docker/Dockerfile.backend
    ports: ["6402:6402"]
    command: celery -A app.workers flower --host=0.0.0.0 --port=6402
    depends_on: [worker]
    env_file: .env

  mcp:
    build: docker/Dockerfile.backend
    ports: ["6403:6403"]
    command: python -m app.api.mcp.server --host 0.0.0.0 --port 6403
    depends_on: [backend]
    env_file: .env

  frontend:
    build: docker/Dockerfile.frontend
    ports: ["6401:6401"]
    command: npm run dev -- --host 0.0.0.0 --port 6401
    volumes: ["./frontend:/app"]

Volumes:
  pgdata:
  redisdata:
```

### docker-compose.prod.yml (production, extends above)

```text
Additional services:
  nginx:
    image: nginx:1.27-alpine
    ports: ["6400:6400"]
    volumes: nginx.conf, frontend static build
    depends_on: [backend, frontend]

  prometheus:
    image: prom/prometheus:v2.54.0
    ports: ["6404:9090"]
    volumes: prometheus.yml config
    command: --config.file=/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana-oss:11-alpine
    ports: ["6405:3000"]
    environment: GF_SECURITY_ADMIN_USER, GF_SECURITY_ADMIN_PASSWORD
    volumes: grafana-data, provisioning configs

Overrides:
  backend:
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:6400
    (no --reload, no volume mount)

  frontend:
    (build stage only — output served by nginx)
```

---

## 3f. pyproject.toml skeleton

```text
[project]
name = "gemini-unified-gateway"
version = "0.1.0"
description = "Unified Gemini web gateway with OpenAI-compatible API"
requires-python = ">=3.11"
dependencies = [
    # --- Upstream adapters ---
    "gemini-webapi[browser]>=1.15.0",
    "gemini-web-mcp-cli>=0.1.0",
    # --- Web framework ---
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "gunicorn>=22.0.0",
    "sse-starlette>=2.1.0",
    "websockets>=13.0",
    "python-multipart>=0.0.12",
    # --- Database ---
    "sqlalchemy[asyncio]>=2.0.35",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "psycopg2-binary>=2.9.9",
    # --- Cache / Queue ---
    "redis[hiredis]>=5.2.0",
    "celery[redis]>=5.4.0",
    "flower>=2.0.0",
    "celery-redbeat>=2.2.0",
    "celery-singleton>=0.3.1",
    # --- Auth / Security ---
    "pyjwt[crypto]>=2.9.0",
    "bcrypt>=4.2.0",
    "cryptography>=43.0.0",
    "passlib[bcrypt]>=1.7.4",
    # --- Schemas ---
    "pydantic>=2.9.0",
    "pydantic-settings>=2.6.0",
    "email-validator>=2.2.0",
    # --- HTTP ---
    "httpx>=0.27.0",
    "aiofiles>=24.1.0",
    "aiohttp>=3.10.0",
    # --- Logging / Metrics ---
    "structlog>=24.4.0",
    "loguru>=0.7.2",
    "prometheus-client>=0.21.0",
    "prometheus-fastapi-instrumentator>=7.0.0",
    # --- CLI ---
    "typer[all]>=0.12.0",
    "rich>=13.9.0",
    # --- MCP ---
    "fastmcp>=2.12.0",
    "mcp>=1.0.0",
    # --- Rate limiting ---
    "slowapi>=0.1.9",
    # --- Utilities ---
    "python-dotenv>=1.0.1",
    "orjson>=3.10.0",
    "tenacity>=9.0.0",
    "cachetools>=5.5.0",
    "croniter>=3.0.0",
    "python-dateutil>=2.9.0",
    "pillow>=10.4.0",
    "browser-cookie3>=0.19.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "pytest-xdist>=3.5.0",
    "factory-boy>=3.3.0",
    "faker>=30.0.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
    "sqlalchemy[mypy]>=2.0.35",
    "pre-commit>=4.0.0",
    "bandit>=1.7.10",
    "locust>=2.31.0",
    "watchfiles>=0.24.0",
]

[project.scripts]
app = "cli.main:app"

[tool.ruff]
target-version = "py311"
line-length = 120
select = ["E","W","F","I","N","UP","S","B","A","C4","PT","RUF"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
plugins = ["pydantic.mypy", "sqlalchemy.ext.mypy.plugin"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--tb=short -q"
```

---

## 3g. package.json skeleton

```text
{
  "name": "gemini-gateway-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 6401",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 0.0.0.0 --port 6401",
    "lint": "eslint .",
    "format": "prettier --write src/"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.28.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.59.0",
    "axios": "^1.7.0",
    "recharts": "^2.13.0",
    "echarts": "^5.5.0",
    "echarts-for-react": "^3.0.2",
    "date-fns": "^4.1.0",
    "lucide-react": "^0.451.0",
    "react-hook-form": "^7.53.0",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.23.0",
    "react-markdown": "^9.0.0",
    "react-syntax-highlighter": "^15.5.0",
    "react-resizable-panels": "^2.1.0",
    "eventsource-parser": "^3.0.0",
    "js-cookie": "^3.0.5",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.5.0",
    "tailwindcss-animate": "^1.0.7",
    "sonner": "^1.5.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "vite-plugin-svgr": "^4.3.0",
    "vite-tsconfig-paths": "^5.1.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/js-cookie": "^3.0.6",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "@tailwindcss/forms": "^0.5.9",
    "@tailwindcss/typography": "^0.5.15",
    "eslint": "^9.12.0",
    "@eslint/js": "^9.12.0",
    "typescript-eslint": "^8.8.0",
    "eslint-plugin-react-hooks": "^5.1.0",
    "eslint-plugin-react-refresh": "^0.4.12",
    "prettier": "^3.3.0",
    "prettier-plugin-tailwindcss": "^0.6.0"
  }
}
```

---

## 3h. Quick install commands

```text
# Backend setup
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend setup
cd frontend
npm install
npx shadcn@latest init          # select: New York style, Zinc color, CSS variables
npx shadcn@latest add button input label card dialog dropdown-menu select \
  tabs table badge avatar toast sheet command separator skeleton switch \
  slider textarea scroll-area alert progress popover form navigation-menu \
  accordion chart
cd ..

# Infrastructure
docker compose up -d             # Postgres:6407 + Redis:6406

# Database
alembic upgrade head
python -m cli.main admin create-user --email admin@local --role admin

# Run everything
./scripts/dev-start.sh
```

---

## 4. Repository layout

```
gemini-unified-gateway/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                          # FastAPI app factory
│   │   ├── config.py                        # Pydantic Settings (env + .env)
│   │   │
│   │   ├── api/
│   │   │   ├── openai/                      # OpenAI-compatible surface
│   │   │   │   ├── chat_completions.py      # POST /v1/chat/completions
│   │   │   │   ├── responses.py             # POST /v1/responses
│   │   │   │   ├── models.py                # GET /v1/models
│   │   │   │   ├── images.py                # POST /v1/images/generations + edits
│   │   │   │   └── files.py                 # GET/POST /v1/files
│   │   │   │
│   │   │   ├── native/                      # Gemini-specific surface
│   │   │   │   ├── videos.py                # POST /native/videos/generations
│   │   │   │   ├── music.py                 # POST /native/music/generations
│   │   │   │   ├── research.py              # POST /native/research
│   │   │   │   ├── gems.py                  # CRUD /native/gems
│   │   │   │   ├── extensions.py            # POST /native/extensions/run
│   │   │   │   ├── limits.py                # GET /native/limits
│   │   │   │   ├── history.py               # GET/DELETE /native/history
│   │   │   │   ├── candidates.py            # POST /native/reply-candidates/select
│   │   │   │   └── jobs.py                  # GET /native/jobs/{id} + /events SSE
│   │   │   │
│   │   │   ├── admin/                       # Control plane surface
│   │   │   │   ├── auth.py                  # Login, logout, refresh, password reset
│   │   │   │   ├── users.py                 # User CRUD + RBAC
│   │   │   │   ├── accounts.py              # Gemini account CRUD
│   │   │   │   ├── api_keys.py              # Consumer API key management
│   │   │   │   ├── analytics.py             # Analytics data endpoints
│   │   │   │   ├── logs.py                  # Log viewer endpoints
│   │   │   │   ├── settings.py              # Server config endpoints
│   │   │   │   ├── parity.py                # Feature parity dashboard data
│   │   │   │   └── packages.py              # Package version + update status
│   │   │   │
│   │   │   ├── mcp/                         # MCP server surface
│   │   │   │   ├── server.py                # SSE + STDIO transport handler
│   │   │   │   ├── tools.py                 # Tool definitions (all features)
│   │   │   │   └── resources.py             # Resource definitions
│   │   │   │
│   │   │   └── health.py                    # /health, /ready, /status
│   │   │
│   │   ├── adapters/                        # Provider isolation
│   │   │   ├── base.py                      # Abstract adapter interface
│   │   │   ├── webapi_adapter.py            # gemini-webapi wrapper
│   │   │   ├── mcpcli_adapter.py            # gemini-web-mcp-cli wrapper
│   │   │   ├── router.py                    # Capability-first request routing
│   │   │   ├── types.py                     # Canonical request/response models
│   │   │   └── fallback.py                  # Fallback/retry orchestration
│   │   │
│   │   ├── auth/                            # Gateway user auth (NOT Gemini auth)
│   │   │   ├── jwt_handler.py
│   │   │   ├── password.py                  # bcrypt hashing
│   │   │   ├── rbac.py                      # Role-based access control
│   │   │   ├── api_key_auth.py              # Bearer token for external consumers
│   │   │   └── dependencies.py              # FastAPI Depends
│   │   │
│   │   ├── accounts/                        # Gemini account management
│   │   │   ├── manager.py                   # Multi-account pool + routing
│   │   │   ├── cookie_store.py              # Encrypted cookie persistence + refresh
│   │   │   ├── apikey_store.py              # API key management
│   │   │   ├── browser_import.py            # browser-cookie3 integration
│   │   │   ├── chrome_login.py              # Automated Chrome login flow
│   │   │   ├── health_checker.py            # Per-account health monitoring
│   │   │   └── crypto.py                    # Fernet encrypt/decrypt for secrets
│   │   │
│   │   ├── models/                          # Model registry
│   │   │   ├── registry.py                  # Model CRUD + capability store
│   │   │   ├── resolver.py                  # Alias → concrete model resolution
│   │   │   ├── discovery.py                 # Auto-discover from both adapters
│   │   │   └── aliases.py                   # Latest-alias management
│   │   │
│   │   ├── jobs/                            # Background job system
│   │   │   ├── manager.py                   # Job lifecycle management
│   │   │   ├── tasks.py                     # Celery/RQ task definitions
│   │   │   └── events.py                    # Job event SSE streaming
│   │   │
│   │   ├── middleware/
│   │   │   ├── request_logger.py            # Structured request/response logging
│   │   │   ├── rate_limiter.py              # Per-key, per-account rate limiting
│   │   │   ├── analytics_collector.py       # Metrics pipeline
│   │   │   ├── cors.py
│   │   │   └── retry.py                     # Upstream retry with backoff
│   │   │
│   │   ├── analytics/
│   │   │   ├── collector.py                 # Raw event ingestion
│   │   │   ├── aggregator.py                # Time-series rollups
│   │   │   ├── parity_tracker.py            # Feature parity scoring
│   │   │   └── cost_estimator.py            # Equivalent API cost tracking
│   │   │
│   │   ├── logging/
│   │   │   ├── structured.py                # JSON structured logger (structlog)
│   │   │   ├── storage.py                   # Log persistence to DB
│   │   │   └── redaction.py                 # Prompt/PII redaction rules
│   │   │
│   │   ├── db/
│   │   │   ├── engine.py                    # Async SQLAlchemy engine
│   │   │   ├── models.py                    # ORM model definitions
│   │   │   └── seed.py                      # Initial admin user + data
│   │   │
│   │   ├── schemas/                         # Pydantic v2 schemas
│   │   │   ├── openai.py                    # OpenAI-compatible types
│   │   │   ├── native.py                    # Gemini-specific types
│   │   │   ├── admin.py                     # Admin/control-plane types
│   │   │   ├── accounts.py                  # Account management types
│   │   │   ├── analytics.py                 # Analytics response types
│   │   │   └── mcp.py                       # MCP tool/resource types
│   │   │
│   │   └── utils/
│   │       ├── sse.py                       # SSE event formatting
│   │       ├── openai_compat.py             # Gemini → OpenAI response transform
│   │       └── package_watcher.py           # Upstream package version monitor
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_adapters/
│   │   │   ├── test_routing/
│   │   │   ├── test_auth/
│   │   │   ├── test_models/
│   │   │   └── test_schemas/
│   │   ├── integration/
│   │   │   ├── test_openai_api/
│   │   │   ├── test_native_api/
│   │   │   ├── test_mcp/
│   │   │   └── test_accounts/
│   │   └── parity/                          # Feature parity regression tests
│   │       ├── test_chat_parity.py
│   │       ├── test_image_parity.py
│   │       └── test_streaming_parity.py
│   │
│   ├── alembic/
│   │   ├── alembic.ini
│   │   └── versions/
│   │
│   ├── cli/                                 # Typer CLI app
│   │   ├── __init__.py
│   │   ├── main.py                          # CLI entry point
│   │   ├── admin_cmds.py                    # User/password management
│   │   ├── account_cmds.py                  # Account add/remove/validate
│   │   ├── model_cmds.py                    # Model refresh/list
│   │   ├── job_cmds.py                      # Job retry/cancel
│   │   ├── log_cmds.py                      # Log tail/export
│   │   └── doctor_cmds.py                   # System health diagnostics
│   │
│   └── pyproject.toml
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx                    # Beautiful login panel
│   │   │   ├── ForgotPassword.tsx
│   │   │   ├── Dashboard.tsx                # Overview metrics
│   │   │   ├── Playground.tsx               # Feature test console
│   │   │   ├── Accounts.tsx                 # Multi-account manager
│   │   │   ├── Models.tsx                   # Model registry + capabilities
│   │   │   ├── Features.tsx                 # Feature parity matrix view
│   │   │   ├── Logs.tsx                     # Request log explorer
│   │   │   ├── Analytics.tsx                # Detailed analytics panels
│   │   │   ├── Admin.tsx                    # Users, RBAC, settings
│   │   │   ├── McpSettings.tsx              # MCP configuration helper
│   │   │   ├── Packages.tsx                 # Package update status
│   │   │   └── Health.tsx                   # System health page
│   │   │
│   │   ├── components/
│   │   │   ├── playground/
│   │   │   │   ├── ChatTester.tsx
│   │   │   │   ├── StreamingChatTester.tsx
│   │   │   │   ├── FileUploadChat.tsx
│   │   │   │   ├── ImageGenerator.tsx
│   │   │   │   ├── ImageEditor.tsx
│   │   │   │   ├── VideoGenerator.tsx
│   │   │   │   ├── MusicGenerator.tsx
│   │   │   │   ├── DeepResearch.tsx
│   │   │   │   ├── GemsTester.tsx
│   │   │   │   ├── ExtensionTester.tsx
│   │   │   │   ├── TemporaryChat.tsx
│   │   │   │   ├── HistoryReplay.tsx
│   │   │   │   └── CandidateSwitcher.tsx
│   │   │   ├── analytics/
│   │   │   ├── accounts/
│   │   │   └── shared/
│   │   │
│   │   └── lib/
│   │       ├── api.ts                       # API client
│   │       ├── auth.ts                      # Auth state management
│   │       └── sse.ts                       # SSE client helpers
│   │
│   └── public/
│
├── scripts/
│   ├── dev-start.sh
│   ├── dev-stop.sh
│   ├── dev-restart.sh
│   ├── migrate.sh
│   ├── worker-start.sh
│   ├── worker-stop.sh
│   └── prod-start.sh
│
├── docker/
│   ├── docker-compose.yml                   # API + frontend + PG + Redis + worker
│   ├── docker-compose.prod.yml              # + Nginx + Grafana + Prometheus
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── Dockerfile.worker
│
├── docs/
│   ├── architecture.md
│   ├── api-mapping.md                       # OpenAI ↔ Gemini endpoint map
│   ├── parity-matrix.md                     # Feature parity tracking
│   ├── auth-guide.md                        # All auth methods documented
│   ├── mcp-integration.md                   # MCP client setup guides
│   └── threat-model.md                      # Security considerations
│
├── .env.example
├── .gitignore
├── README.md
└── LICENSE
```

---

## 5. Database schema — entity list

### Core entities

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `users` | Gateway users (admin login) | id, email, password_hash, role, status, created_at |
| `password_reset_tokens` | One-time reset tokens | id, user_id, token_hash, expires_at, used_at |
| `consumer_api_keys` | API keys for external clients | id, user_id, key_hash, label, scopes, rate_limit, status |

### Account entities

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `accounts` | Gemini accounts (NOT user accounts) | id, label, owner_user_id, provider, status, region_hint, language_hint, chrome_required, health_status |
| `account_auth_methods` | Auth credentials per account | id, account_id, auth_type (cookie/apikey/browser/chrome), encrypted_credentials, last_refreshed, expires_at |
| `account_profiles` | Multiple Google profiles per account | id, account_id, profile_name, is_default, metadata |

### Model entities

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `models` | Discovered model registry | id, provider_model_name, display_name, family, source_provider, status, discovered_at |
| `model_aliases` | Stable aliases (gemini-pro-latest) | id, alias, resolved_model_id, priority, updated_at |
| `model_capabilities` | Per-model feature flags | id, model_id, text, images, image_edit, video, music, research, extensions, streaming, code_exec, thinking, max_tokens |

### Request/analytics entities

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `requests` | Every API request | id, user_id, account_id, provider, endpoint, model_alias, resolved_model, feature_type, stream_mode, latency_ms, status_code, retry_count, prompt_hash, created_at |
| `request_events` | Per-request event timeline | id, request_id, event_type, timestamp, metadata |
| `usage_snapshots` | Periodic quota captures | id, account_id, snapshot_at, limits_json |

### Job entities

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `jobs` | Long-running tasks | id, request_id, account_id, job_type (video/music/research), status, progress_pct, result_url, error, created_at, completed_at |

### Admin entities

| Table | Purpose | Key columns |
|-------|---------|-------------|
| `admin_audit_logs` | Admin action audit trail | id, user_id, action, target, metadata, timestamp |
| `feature_parity_results` | Parity test results | id, feature, provider, test_status, tested_at, notes |

---

## 6. API endpoint specification

### OpenAI-compatible endpoints (/v1/...)

| Method | Path | Description | SSE? |
|--------|------|-------------|------|
| GET | /v1/models | List all models with capabilities | no |
| GET | /v1/models/{id} | Single model detail | no |
| POST | /v1/chat/completions | Chat completion (stream=true for SSE) | yes |
| POST | /v1/responses | Responses API (OpenAI format) | yes |
| POST | /v1/images/generations | Generate images | no |
| POST | /v1/images/edits | Edit images | no |
| GET | /v1/files | List uploaded files | no |
| POST | /v1/files | Upload a file | no |

### Native Gemini endpoints (/native/...)

| Method | Path | Description | SSE? |
|--------|------|-------------|------|
| POST | /native/videos/generations | Start video generation (returns job_id) | no |
| POST | /native/music/generations | Start music generation (returns job_id) | no |
| POST | /native/research | Start deep research (returns job_id) | no |
| GET | /native/jobs/{id} | Poll job status + result | no |
| GET | /native/jobs/{id}/events | Stream job progress events | yes |
| GET | /native/limits | Check usage limits/quotas | no |
| GET | /native/gems | List gems | no |
| POST | /native/gems | Create gem | no |
| PUT | /native/gems/{id} | Update gem | no |
| DELETE | /native/gems/{id} | Delete gem | no |
| POST | /native/extensions/run | Invoke a Gemini extension | no |
| GET | /native/history | List conversation history | no |
| DELETE | /native/history/{chat_id} | Delete a conversation | no |
| POST | /native/reply-candidates/select | Switch reply candidate | no |
| POST | /native/temporary-chat | One-off chat with no history | yes |

### Admin endpoints (/admin/...)

| Method | Path | Description |
|--------|------|-------------|
| POST | /admin/login | JWT login |
| POST | /admin/logout | Invalidate token |
| POST | /admin/refresh | Refresh JWT |
| POST | /admin/password/reset | Request password reset |
| POST | /admin/password/set | Set new password with token |
| GET | /admin/users | List users (admin only) |
| POST | /admin/users | Create user |
| PATCH | /admin/users/{id} | Update user role/status |
| DELETE | /admin/users/{id} | Disable user |
| GET | /admin/accounts | List Gemini accounts |
| POST | /admin/accounts | Add Gemini account |
| PATCH | /admin/accounts/{id} | Update account credentials |
| DELETE | /admin/accounts/{id} | Remove account |
| GET | /admin/accounts/{id}/health | Account health detail |
| POST | /admin/accounts/{id}/validate | Force-validate credentials |
| GET | /admin/api-keys | List consumer API keys |
| POST | /admin/api-keys | Create consumer API key |
| DELETE | /admin/api-keys/{id} | Revoke API key |
| GET | /admin/analytics/overview | Dashboard summary |
| GET | /admin/analytics/requests | Request metrics (time-series) |
| GET | /admin/analytics/models | Per-model analytics |
| GET | /admin/analytics/accounts | Per-account analytics |
| GET | /admin/analytics/errors | Error breakdown |
| GET | /admin/analytics/features | Feature usage breakdown |
| GET | /admin/analytics/parity | Feature parity score |
| GET | /admin/analytics/cost | Cost proxy estimates |
| GET | /admin/logs | Paginated request logs |
| GET | /admin/logs/{id} | Single request detail + event timeline |
| POST | /admin/logs/{id}/replay | Replay a request |
| GET | /admin/settings | Server configuration |
| PUT | /admin/settings | Update server configuration |
| GET | /admin/packages | Upstream package versions + update status |
| POST | /admin/packages/refresh | Force check for package updates |
| GET | /admin/audit | Admin audit log |

### MCP endpoints (/mcp/...)

| Method | Path | Description |
|--------|------|-------------|
| GET | /mcp/sse | SSE transport for MCP clients |
| POST | /mcp/messages | HTTP transport for MCP |
| GET | /mcp/tools | List registered MCP tools |

### Utility endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness check |
| GET | /ready | Readiness (all dependencies up) |
| GET | /status | Public status page data |
| GET | /docs | Swagger UI |
| GET | /redoc | ReDoc |

---

## 7. SSE streaming specification

### Chat streaming (OpenAI-compatible)

Event types for /v1/chat/completions with stream=true:

- `message.start` — initial metadata (model, id)
- `message.delta` — incremental content token
- `tool.delta` — tool call incremental
- `usage` — token usage summary
- `message.completed` — final signal
- `message.error` — error with code + message

Format follows OpenAI exactly: `data: {"id":"...","choices":[{"delta":{"content":"..."}}]}`

### Job streaming (native)

Event types for /native/jobs/{id}/events:

- `progress` — percentage + status message
- `warning` — non-fatal issue
- `completed` — result URL + metadata
- `error` — failure details

---

## 8. Capability-first routing logic

### Decision tree per request

```
1. Parse requested model (resolve alias if needed)
2. Determine required capability (chat? image_gen? video_gen? research?)
3. Query capability matrix: which adapters support this feature?
4. Filter by: account health → auth state → quota availability → region
5. If both adapters qualify: use preference order (configurable per feature)
6. If only one qualifies: use that adapter
7. If none qualify: return 503 with clear error
8. On adapter failure: if fallback adapter available, retry there
9. Log: adapter used, fallback attempted, final result
```

### What "capability flags" track per account

- auth_valid: bool
- cookie_fresh: bool
- chrome_available: bool
- region: str
- quota_remaining: int or null
- supports_chat: bool
- supports_streaming: bool
- supports_image_gen: bool
- supports_image_edit: bool
- supports_video_gen: bool
- supports_music_gen: bool
- supports_research: bool
- supports_extensions: bool
- supports_gems: bool
- supports_limits: bool
- supports_history: bool
- last_health_check: datetime
- last_successful_request: datetime
- consecutive_failures: int

---

## 9. Model registry and latest-alias system

### Alias examples

| Alias | Resolution strategy |
|-------|-------------------|
| gemini-pro-latest | Highest-ranked healthy Pro model |
| gemini-flash-latest | Highest-ranked healthy Flash model |
| gemini-thinking-latest | Highest-ranked thinking-capable model |
| gemini-image-latest | Best available image generation model |
| gemini-video-latest | Best available video generation model |
| gemini-music-latest | Best available music generation model |
| gemini-research-latest | Best available research-capable model |

### Auto-discovery schedule

- On startup: full discovery from both adapters
- Every 6 hours: refresh model list
- On package update detection: immediate re-discovery
- Admin can force refresh via GUI or CLI
- Unknown model names are passed through to adapters as-is (gemini-webapi supports custom model strings)

### Logging

Every request logs both the alias used AND the resolved concrete model name. This enables debugging when aliases shift.

---

## 10. Multi-account management

### Supported auth methods

| Method | Adapter | How it works |
|--------|---------|-------------|
| Manual cookie paste | webapi | User provides __Secure-1PSID + __Secure-1PSIDTS via GUI or CLI |
| Cookie file | webapi | User provides JSON file with cookies |
| Browser import | webapi | browser-cookie3 reads cookies from local Chrome/Firefox |
| Automated Chrome login | mcp-cli | Headless Chrome flow with Google login |
| API key | both (for CLI ops) | GEMINI_API_KEY for CLI-backed features |
| Profile reuse | mcp-cli | Reuse existing Chrome profile |

### CLI commands for account management

- `app accounts add --type cookie --interactive` → paste cookies in terminal
- `app accounts add --type cookie --file /path/to/cookies.json`
- `app accounts add --type browser --browser chrome`
- `app accounts add --type chrome-login` → launches Chrome flow
- `app accounts add --type apikey --key "..."
- `app accounts validate --id 3` → test account health immediately
- `app accounts list` → show all accounts with health status
- `app accounts remove --id 3`

### GUI account management

- Account list with health badges (green/yellow/red)
- "Add Account" wizard with tabs for each auth method
- Cookie paste textarea with instant validation
- Browser import one-click button (same machine only)
- Per-account settings: label, region hint, language, chrome flag
- Per-account quota display (where available)
- Credential rotation/refresh button
- Account health history chart

### Pool routing strategy

- Round-robin across healthy accounts (default)
- Sticky sessions for multi-turn chats (same account for conversation continuity)
- Auto-failover on 429 / auth failure / timeout
- Per-account rate tracking to avoid burning one account
- Configurable account preferences per feature type
- Health check interval: 60s (configurable)

---

## 11. Analytics — detailed panel specifications

### 11.1 Overview dashboard

- TODO: Total requests today / this week / this month (counter cards)
- TODO: Success rate gauge (2xx vs 4xx/5xx)
- TODO: Average latency with p50, p95, p99 breakdown
- TODO: Active healthy accounts / total accounts
- TODO: Most-used model badge
- TODO: Streaming vs non-streaming ratio
- TODO: Feature usage distribution (pie: chat, image, video, music, research, extensions)

### 11.2 Request analytics

- TODO: Requests over time line chart (1h / 6h / 24h / 7d / 30d toggles)
- TODO: Request distribution by endpoint (stacked bar)
- TODO: Latency distribution histogram
- TODO: Error rate over time with trend line
- TODO: Top error codes breakdown table
- TODO: Streaming chunk latency percentiles

### 11.3 Model analytics

- TODO: Requests per model bar chart
- TODO: Latency comparison per model
- TODO: Feature usage per model heatmap
- TODO: Model availability uptime percentage
- TODO: Model discovery timeline (when models appeared/disappeared)

### 11.4 Account analytics

- TODO: Requests per account bar chart
- TODO: Rate limit hits per account over time
- TODO: Cookie refresh history timeline
- TODO: Account health timeline (healthy/degraded/unhealthy bands)
- TODO: Error distribution per account
- TODO: Quota depletion trends (where available)

### 11.5 Feature analytics

- TODO: Usage counts per feature type over time
- TODO: Image/video/music generation volume
- TODO: Deep research session count and average duration
- TODO: Extension invocation breakdown
- TODO: Gems usage frequency

### 11.6 Feature parity dashboard

- TODO: Matrix view: features as rows, adapters as columns
- TODO: Color-coded: green (working), yellow (partial), red (broken), gray (unsupported)
- TODO: Last-tested timestamp per cell
- TODO: Parity score percentage per adapter
- TODO: One-click "test now" per feature
- TODO: Historical parity trend line

### 11.7 Cost proxy dashboard

- TODO: Assign internal token weights per model
- TODO: Estimated cost if these were paid API calls
- TODO: Cost by user / by account / by model
- TODO: Daily/monthly cost trend
- TODO: Budget alerts (configurable thresholds)

### 11.8 Request detail view

- TODO: Full request metadata display
- TODO: Expandable event timeline: accepted → routed → auth checked → upload started → provider call → partial chunks → completed/error → finalized
- TODO: Raw provider trace ID
- TODO: Redacted prompt hash (full prompt only in admin debug mode)
- TODO: "Replay this request" button
- TODO: "Compare with other adapter" button (request diff tool)

### 11.9 Log viewer

- TODO: Real-time streaming via WebSocket
- TODO: Filter by: endpoint, model, account, status code, time range, user, provider
- TODO: Request/response body inspection (with redaction controls)
- TODO: Latency breakdown per request stage
- TODO: Export to CSV / JSON

---

## 12. GUI page specifications

### 12.1 Login page

- TODO: Clean, modern design with subtle gradient or illustration
- TODO: Email + password form
- TODO: "Forgot password?" link → reset flow
- TODO: Optional "remember me" checkbox
- TODO: Rate-limited login attempts (5 per minute)
- TODO: Clear error messages for wrong credentials

### 12.2 Dashboard

- TODO: Summary cards row (requests, success rate, latency, accounts)
- TODO: Requests chart (last 24h default)
- TODO: Feature distribution pie
- TODO: Recent errors list
- TODO: Quick-access buttons to playground, accounts, logs
- TODO: System health indicator

### 12.3 Playground (feature test console)

Every upstream feature must be testable from GUI:

- TODO: Chat tab — model selector, system prompt, message input, response display
- TODO: Streaming chat tab — same but with live token streaming
- TODO: File upload chat tab — drag-drop files + message
- TODO: Image generation tab — prompt, style options, result gallery
- TODO: Image editing tab — upload image, edit prompt, before/after display
- TODO: Video generation tab — prompt, aspect ratio, progress bar, video player
- TODO: Music generation tab — prompt, duration, progress bar, audio player
- TODO: Deep research tab — query input, progress tracker, result markdown viewer
- TODO: Gems tab — list, create, test with gem applied
- TODO: Extensions tab — select extension (Maps/YouTube/Flights/Hotels), input, result
- TODO: Temporary chat tab — one-off with explicit "no history" badge
- TODO: History tab — browse past conversations, replay
- TODO: Candidate switcher — view alternative responses, select preferred

Each playground tab:
- TODO: Account selector (which Gemini account to use)
- TODO: Model selector (with capability filter — only show models that support this feature)
- TODO: Provider toggle (force webapi / force mcp-cli / auto)
- TODO: Raw response viewer toggle
- TODO: Latency display
- TODO: Copy response button

### 12.4 Accounts page

- TODO: Account cards with health indicator, last request time, quota info
- TODO: Add account wizard (multi-step, auth method tabs)
- TODO: Edit credentials modal
- TODO: Force validate button
- TODO: Account health history sparkline
- TODO: Delete account with confirmation

### 12.5 Models page

- TODO: Searchable/filterable model table
- TODO: Capability badges per model (text, image, video, music, research, extensions, streaming)
- TODO: Source badge (webapi / mcp-cli / both)
- TODO: Alias list with current resolution
- TODO: "Refresh models" button
- TODO: Last-discovered timestamp

### 12.6 Features (parity matrix) page

- TODO: Full parity matrix grid
- TODO: Per-feature test buttons
- TODO: Historical parity trend
- TODO: Export parity report

### 12.7 Admin page

- TODO: User management table (create, edit role, disable)
- TODO: RBAC configuration
- TODO: Consumer API key management
- TODO: Server settings form
- TODO: Audit log table
- TODO: Package version display with "update available" badges
- TODO: MCP configuration helper (generates JSON configs for Claude Desktop, Cursor, etc.)

---

## 13. CLI command specification (Typer)

### User/auth management
- TODO: `app admin create-user --email --role` (admin/operator/viewer/developer)
- TODO: `app admin reset-password --email` (outputs one-time token OR sets temp password)
- TODO: `app admin disable-user --email`
- TODO: `app admin list-users`

### Account management
- TODO: `app accounts add --type cookie --interactive` (paste in terminal)
- TODO: `app accounts add --type cookie --file PATH`
- TODO: `app accounts add --type browser --browser chrome`
- TODO: `app accounts add --type chrome-login`
- TODO: `app accounts add --type apikey --key KEY`
- TODO: `app accounts validate --id ID`
- TODO: `app accounts list`
- TODO: `app accounts remove --id ID`
- TODO: `app accounts health`

### Model management
- TODO: `app models refresh` (force re-discovery)
- TODO: `app models list` (show all with capabilities)
- TODO: `app models aliases` (show alias → resolution table)

### Operations
- TODO: `app jobs list` (show pending/running jobs)
- TODO: `app jobs retry --id ID`
- TODO: `app jobs cancel --id ID`
- TODO: `app logs tail` (stream live logs to terminal)
- TODO: `app logs export --from DATE --to DATE --format json`
- TODO: `app sync package-features` (re-scan upstream packages for new features)
- TODO: `app doctor` (full system health diagnostic)

---

## 14. MCP server tool registry

All gateway features exposed as MCP tools:

### Chat tools
- TODO: `chat` — send a message, get response
- TODO: `chat_stream` — streaming chat (via SSE)
- TODO: `temporary_chat` — no-history chat

### Generation tools
- TODO: `generate_image` — text-to-image
- TODO: `edit_image` — image editing
- TODO: `generate_video` — text-to-video (returns job_id)
- TODO: `generate_music` — text-to-music (returns job_id)
- TODO: `deep_research` — research session (returns job_id)

### File tools
- TODO: `upload_file` — upload for chat context
- TODO: `list_files` — list uploaded files

### Information tools
- TODO: `list_models` — models + capabilities
- TODO: `list_gems` — available gems
- TODO: `list_limits` — usage quotas
- TODO: `list_accounts` — available accounts + health
- TODO: `health_check` — system health

### Job tools
- TODO: `check_job` — poll job status
- TODO: `cancel_job` — cancel running job

### Extension tools
- TODO: `run_extension` — invoke Gemini extension (Maps, YouTube, etc.)

### History tools
- TODO: `list_history` — conversation history
- TODO: `delete_history` — delete a conversation
- TODO: `select_candidate` — switch reply candidate

### MCP transport
- TODO: SSE transport at /mcp/sse on 0.0.0.0:6403 (for network clients)
- TODO: STDIO transport (for local Claude Desktop / Claude Code)
- TODO: Auth via gateway API key (all MCP calls go through gateway, not direct to Gemini)

### MCP client configuration examples

Claude Desktop / Cursor / Windsurf config:
```text
{
  "mcpServers": {
    "gemini-gateway": {
      "url": "http://0.0.0.0:6403/mcp/sse",
      "env": { "GATEWAY_API_KEY": "sk-your-key" }
    }
  }
}
```

Config file locations:
- Claude Desktop macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
- Claude Desktop Windows: %APPDATA%\Claude\claude_desktop_config.json
- Claude Desktop Linux: ~/.config/claude/claude_desktop_config.json
- Cursor: $HOME/.cursor/mcp.json
- Windsurf: $HOME/.codeium/windsurf/mcp_config.json
- Claude Code: claude mcp add gemini-gateway --url http://0.0.0.0:6403/mcp/sse

---

## 15. Dev scripts specification

> Full behavioral spec in section 3d. Summary of port-mapped URLs below.

### dev-start.sh
- TODO: Create Python venv if missing (python3.11 -m venv .venv or uv venv)
- TODO: Install backend dependencies (pip install -e ".[dev]" or uv sync)
- TODO: Install frontend dependencies (npm install --prefix frontend/)
- TODO: Start Postgres on 0.0.0.0:6407 + Redis on 0.0.0.0:6406 via docker-compose
- TODO: Wait for PG + Redis healthchecks to pass
- TODO: Run Alembic migrations (alembic upgrade head)
- TODO: Seed admin user if first run
- TODO: Start uvicorn on 0.0.0.0:6400 with --reload
- TODO: Start Celery worker (broker redis://0.0.0.0:6406/1)
- TODO: Start Flower on 0.0.0.0:6402
- TODO: Start MCP SSE server on 0.0.0.0:6403
- TODO: Start frontend vite dev server on 0.0.0.0:6401
- TODO: Start WebSocket log server on 0.0.0.0:6408
- TODO: Store all PIDs in .dev.pids
- TODO: Print startup banner with all URLs:
  ```
  ┌────────────────────────────────────────────────┐
  │  Gemini Unified Gateway — DEV MODE             │
  ├────────────────────────────────────────────────┤
  │  API + Swagger   http://0.0.0.0:6400/docs     │
  │  ReDoc           http://0.0.0.0:6400/redoc    │
  │  Frontend        http://0.0.0.0:6401          │
  │  Flower          http://0.0.0.0:6402          │
  │  MCP SSE         http://0.0.0.0:6403          │
  │  Prometheus      http://0.0.0.0:6404          │
  │  Grafana         http://0.0.0.0:6405          │
  │  PostgreSQL      0.0.0.0:6407                 │
  │  Redis           0.0.0.0:6406                 │
  │  Live Logs WS    ws://0.0.0.0:6408            │
  └────────────────────────────────────────────────┘
  ```

### dev-stop.sh
- TODO: Read .dev.pids, kill each PID
- TODO: Optionally stop docker-compose stack (with --all flag)
- TODO: Remove .dev.pids

### dev-restart.sh
- TODO: Run dev-stop.sh, sleep 2, run dev-start.sh

### migrate.sh
- TODO: Run alembic upgrade head (using DATABASE_URL_SYNC on 0.0.0.0:6407)
- TODO: Show current revision

### worker-start.sh / worker-stop.sh
- TODO: Start/stop Celery worker + Flower independently

---

## 16. Security design

### Credential encryption
- TODO: All Gemini cookies and API keys encrypted at rest using Fernet with a master key
- TODO: Master key sourced from environment variable (never committed)
- TODO: Rotation support: re-encrypt all credentials with new master key

### Log redaction
- TODO: Default mode: store SHA-256 prompt hash only, no prompt text
- TODO: Debug mode (admin toggle): store encrypted full prompt/response for troubleshooting
- TODO: Auto-expire debug payloads after configurable TTL
- TODO: PII detection and auto-scrub for common patterns

### Auth separation
- TODO: Gateway user auth: JWT + bcrypt (for web dashboard / admin)
- TODO: Consumer auth: Bearer API keys (for OpenAI-compatible clients)
- TODO: Gemini account auth: cookies / API keys (for upstream providers)
- TODO: These three auth systems are completely independent

### RBAC roles
- `admin`: full access — users, accounts, settings, audit
- `operator`: accounts, models, jobs, logs, analytics
- `viewer`: read-only dashboard, analytics, logs
- `developer`: playground, models, own API keys

---

## 17. Observability

### Logging
- TODO: JSON structured logging via structlog
- TODO: Request correlation IDs across all layers
- TODO: Log levels: DEBUG (development), INFO (production), WARNING, ERROR
- TODO: Log rotation and retention policy (configurable days)

### Metrics (Prometheus)
- TODO: request_total (by endpoint, method, status, provider)
- TODO: request_duration_seconds (histogram by endpoint)
- TODO: active_connections (gauge)
- TODO: account_health (gauge per account, 0/1)
- TODO: job_queue_depth (gauge by job type)
- TODO: model_discovery_total
- TODO: cookie_refresh_total (by account, success/failure)
- TODO: sse_active_streams (gauge)

### Alerting (Grafana)
- TODO: Alert on: error rate > 10% for 5 min
- TODO: Alert on: all accounts unhealthy
- TODO: Alert on: job queue backlog > 50
- TODO: Alert on: cookie refresh failures > 3 consecutive

### Canary tests
- TODO: Synthetic request every 5 minutes to each adapter
- TODO: Tests: basic chat, streaming, image gen (per adapter capability)
- TODO: Results feed into health checker and parity dashboard

---

## 18. Webhook / event dispatch

- TODO: Configurable webhook URLs per event type
- TODO: Events: job_completed, job_failed, account_unhealthy, account_recovered, error_spike, quota_low, package_update_available
- TODO: Slack + Discord webhook format support
- TODO: Retry with exponential backoff on delivery failure
- TODO: Webhook delivery log in admin panel

---

## 19. Package update watcher

- TODO: Background task checks PyPI for gemini-webapi and gemini-web-mcp-cli versions
- TODO: Check interval: every 12 hours
- TODO: Compare installed vs latest
- TODO: If update available: badge in admin GUI + optional webhook
- TODO: On update (manual or auto): trigger model re-discovery
- TODO: Changelog diff display in admin panel

---

## 20. Risk register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Google changes web API behavior | Adapters break | Parity tests detect quickly; fallback to other adapter; canary tests; webhook alerts |
| One upstream package abandoned | Feature loss | Isolated adapters allow swapping; abstract interface unchanged |
| Cookie expiry during long session | Auth failure mid-request | Auto-refresh in background; retry with fresh cookie; health checker pre-validates |
| Region-locked features | Feature unavailable for some accounts | Capability flags per account; route around; clear error messages |
| Chrome/BotGuard required | Some features fail without headless Chrome | Track chrome_required flag per account; document which features need it |
| Rate limiting by Google | 429 errors | Distribute across account pool; per-account rate tracking; backoff |
| OpenAI spec gaps | Video/music/research don't map to OpenAI | Native endpoints; clear docs; MCP tools cover everything |
| Alpha upstream instability | Unexpected breakage | Pin versions; test before upgrading; rollback plan |

---

## 21. Implementation phases — detailed TODOs

### Phase 1 — Foundation (Week 1-2)

**Backend scaffolding**
- [ ] Initialize git repo with monorepo structure
- [ ] Create Python 3.11 venv setup (support both pip and uv)
- [ ] Write pyproject.toml with all dependencies and [dev] extras
- [ ] Configure ruff, mypy, pytest in pyproject.toml
- [ ] Create .env.example with all config variables
- [ ] Create .gitignore

**FastAPI app**
- [ ] Create FastAPI app factory with lifespan handler
- [ ] Create Pydantic Settings config (env + .env loading)
- [ ] Setup CORS middleware
- [ ] Create /health and /ready endpoints
- [ ] Verify Swagger UI at /docs and ReDoc at /redoc
- [ ] Configure structlog JSON logging

**Database**
- [ ] Create async SQLAlchemy engine
- [ ] Define all ORM models (users, accounts, models, requests, jobs, etc.)
- [ ] Initialize Alembic with async support
- [ ] Create initial migration
- [ ] Write DB seed script (admin user)

**Auth system**
- [ ] Implement JWT handler (create, validate, refresh)
- [ ] Implement bcrypt password hashing
- [ ] Create login/logout/refresh endpoints
- [ ] Create FastAPI auth dependencies (current_user, require_role)
- [ ] Implement RBAC decorator/dependency
- [ ] Implement Bearer API key auth for external consumers

**Password reset**
- [ ] Create password reset token generation/validation
- [ ] Create CLI command: `app admin reset-password`
- [ ] Create admin API endpoint for password reset
- [ ] Implement token expiry and one-time-use

**CLI foundation**
- [ ] Setup Typer app with command groups
- [ ] Implement `app admin create-user`
- [ ] Implement `app admin reset-password`
- [ ] Implement `app doctor` (basic checks)

**Dev scripts**
- [ ] Write dev-start.sh (all services on 0.0.0.0:6400-6408, see section 3d)
- [ ] Write dev-stop.sh (kill all PIDs from .dev.pids)
- [ ] Write dev-restart.sh (stop + start)
- [ ] Write migrate.sh (alembic upgrade head)
- [ ] Write worker-start.sh / worker-stop.sh
- [ ] Write docker-compose.yml (PG on 6407, Redis on 6406, see section 3e)
- [ ] Write docker-compose.prod.yml (adds Nginx, Prometheus 6404, Grafana 6405)

**Tests**
- [ ] Setup pytest + pytest-asyncio
- [ ] Setup test database fixture
- [ ] Write auth unit tests
- [ ] Write health endpoint integration test

---

### Phase 2 — Provider adapters (Week 2-3)

**Abstract adapter interface**
- [ ] Define base adapter class with all method signatures
- [ ] Define canonical request/response Pydantic types
- [ ] Define capability metadata type
- [ ] Define provider health state machine

**gemini-webapi adapter**
- [ ] Install gemini-webapi in venv
- [ ] Implement chat_completion method
- [ ] Implement stream method (async generator → SSE)
- [ ] Implement generate_image method
- [ ] Implement edit_image method
- [ ] Implement list_models method
- [ ] Implement gems CRUD methods
- [ ] Implement extensions_run method
- [ ] Implement history CRUD methods
- [ ] Implement temporary_chat method
- [ ] Implement reply_candidates method
- [ ] Implement file upload method
- [ ] Implement thought/reasoning retrieval
- [ ] Add health check method
- [ ] Add capability flag reporting

**gemini-web-mcp-cli adapter**
- [ ] Install gemini-web-mcp-cli in venv
- [ ] Implement chat_completion method
- [ ] Implement generate_image method
- [ ] Implement generate_video method (returns job)
- [ ] Implement generate_music method (returns job)
- [ ] Implement deep_research method (returns job)
- [ ] Implement list_limits method
- [ ] Implement list_models method
- [ ] Implement gems methods
- [ ] Implement file upload method
- [ ] Implement multi-profile support
- [ ] Add health check method
- [ ] Add capability flag reporting
- [ ] Handle Chrome/BotGuard requirement detection

**Capability-first router**
- [ ] Implement routing decision tree
- [ ] Implement adapter preference configuration per feature
- [ ] Implement fallback logic with retry
- [ ] Log routing decisions (adapter chosen, fallback attempted)

**Response normalization**
- [ ] Implement Gemini → canonical response transform
- [ ] Implement canonical → OpenAI response transform
- [ ] Preserve raw provider payload alongside normalized output
- [ ] Extract provider trace IDs where available

**Tests**
- [ ] Unit tests for each adapter method (mocked upstream)
- [ ] Unit tests for routing logic
- [ ] Unit tests for response normalization

---

### Phase 3 — OpenAI-compatible layer (Week 3-4)

**Endpoints**
- [ ] Implement POST /v1/chat/completions (non-streaming)
- [ ] Implement POST /v1/chat/completions (streaming SSE)
- [ ] Implement POST /v1/responses
- [ ] Implement GET /v1/models
- [ ] Implement GET /v1/models/{id}
- [ ] Implement POST /v1/images/generations
- [ ] Implement POST /v1/images/edits
- [ ] Implement GET /v1/files
- [ ] Implement POST /v1/files

**SSE streaming**
- [ ] Implement SSE event formatter (OpenAI format)
- [ ] Implement async generator → SSE response
- [ ] Handle stream interruption/cleanup
- [ ] Implement heartbeat for long-lived connections

**Schemas**
- [ ] Define all OpenAI-compatible Pydantic request models
- [ ] Define all OpenAI-compatible Pydantic response models
- [ ] Validate against actual OpenAI API spec
- [ ] Ensure Swagger UI shows clean, browsable schemas

**Tests**
- [ ] Integration tests with real OpenAI SDK client
- [ ] Streaming tests (capture SSE events)
- [ ] Error response format tests

---

### Phase 4 — Native Gemini layer (Week 4-5)

**Endpoints**
- [ ] Implement POST /native/videos/generations
- [ ] Implement POST /native/music/generations
- [ ] Implement POST /native/research
- [ ] Implement GET /native/jobs/{id}
- [ ] Implement GET /native/jobs/{id}/events (SSE)
- [ ] Implement GET /native/limits
- [ ] Implement CRUD /native/gems
- [ ] Implement POST /native/extensions/run
- [ ] Implement GET/DELETE /native/history
- [ ] Implement POST /native/reply-candidates/select
- [ ] Implement POST /native/temporary-chat

**Job system**
- [ ] Setup Celery (or RQ) with Redis broker
- [ ] Create video generation task
- [ ] Create music generation task
- [ ] Create deep research task
- [ ] Implement job status polling endpoint
- [ ] Implement job event SSE endpoint
- [ ] Implement job timeout and cancellation
- [ ] Implement job retry with exponential backoff

**Schemas**
- [ ] Define all native Pydantic request/response models
- [ ] Ensure clean Swagger grouping (separate from OpenAI group)

**Tests**
- [ ] Job lifecycle tests (create → poll → complete)
- [ ] Job failure and retry tests
- [ ] Native endpoint integration tests

---

### Phase 5 — Account control plane (Week 5-6)

**Account management**
- [ ] Implement account CRUD endpoints
- [ ] Implement encrypted credential storage (Fernet)
- [ ] Implement cookie paste flow (GUI + CLI)
- [ ] Implement cookie file import
- [ ] Implement browser-cookie3 import
- [ ] Implement automated Chrome login flow
- [ ] Implement API key storage
- [ ] Implement account validation endpoint
- [ ] Implement multi-profile support (mcp-cli profiles)

**Pool manager**
- [ ] Implement round-robin account selection
- [ ] Implement sticky sessions for multi-turn chats
- [ ] Implement auto-failover on auth/rate errors
- [ ] Implement per-account rate tracking
- [ ] Implement configurable feature → account preferences

**Health checker**
- [ ] Implement periodic health check task (60s interval)
- [ ] Implement health state transitions (healthy → degraded → unhealthy → recovering)
- [ ] Track consecutive failures per account
- [ ] Auto-disable account after N consecutive failures
- [ ] Auto-re-enable after successful health check

**Cookie lifecycle**
- [ ] Implement background cookie refresh (webapi's auto-refresh)
- [ ] Track cookie expiry times
- [ ] Alert before cookie expiration
- [ ] Handle cookie refresh failure gracefully

**Model registry**
- [ ] Implement model discovery from both adapters
- [ ] Implement model CRUD in database
- [ ] Implement alias management
- [ ] Implement latest-alias resolution logic
- [ ] Implement scheduled refresh (every 6 hours)
- [ ] Implement pass-through for unknown model names

**Consumer API keys**
- [ ] Implement API key generation (with scopes)
- [ ] Implement API key auth middleware
- [ ] Implement per-key rate limits
- [ ] Implement key revocation

**CLI commands**
- [ ] Implement all `app accounts` commands
- [ ] Implement all `app models` commands
- [ ] Implement `app admin` user management commands

**Tests**
- [ ] Account CRUD tests
- [ ] Encryption round-trip tests
- [ ] Pool routing tests
- [ ] Health checker state machine tests
- [ ] Model resolution tests

---

### Phase 6 — Logging, analytics, observability (Week 6-7)

**Request logging**
- [ ] Implement request logging middleware (structlog)
- [ ] Implement request correlation IDs
- [ ] Implement log storage to database
- [ ] Implement prompt redaction (SHA-256 hash by default)
- [ ] Implement optional encrypted full payload logging (admin toggle)
- [ ] Implement request event timeline recording

**Analytics**
- [ ] Implement analytics collector (ingests from request middleware)
- [ ] Implement time-series aggregation (hourly, daily, monthly rollups)
- [ ] Implement per-model metrics
- [ ] Implement per-account metrics
- [ ] Implement per-feature metrics
- [ ] Implement cost proxy calculator
- [ ] Implement all analytics API endpoints

**Feature parity tracker**
- [ ] Implement parity test runner (tests each feature on each adapter)
- [ ] Store results in feature_parity_results table
- [ ] Implement parity score calculation
- [ ] Implement parity API endpoint

**Observability**
- [ ] Integrate Prometheus client
- [ ] Expose /metrics endpoint
- [ ] Define all metric counters/gauges/histograms
- [ ] Create Grafana dashboard templates
- [ ] Implement alerting rules

**Package watcher**
- [ ] Implement PyPI version checker for both upstream packages
- [ ] Implement check schedule (every 12 hours)
- [ ] Implement admin notification on update available
- [ ] Implement post-update model re-discovery trigger

**Log viewer API**
- [ ] Implement paginated log query endpoint
- [ ] Implement log filters (endpoint, model, account, status, time range)
- [ ] Implement single request detail with event timeline
- [ ] Implement request replay endpoint
- [ ] Implement log export (CSV, JSON)

**Canary tests**
- [ ] Implement synthetic request scheduler (every 5 min)
- [ ] Test basic chat on each adapter
- [ ] Test streaming on each adapter
- [ ] Feed results into health checker and parity dashboard

**Tests**
- [ ] Analytics aggregation tests
- [ ] Log redaction tests
- [ ] Parity scoring tests

---

### Phase 7 — Web GUI (Week 7-9)

**Frontend setup**
- [ ] Initialize React + Vite + TypeScript project
- [ ] Install and configure Tailwind CSS + shadcn/ui
- [ ] Setup ECharts or Recharts
- [ ] Create API client module (with auth interceptors)
- [ ] Create SSE client utility
- [ ] Setup routing (React Router)
- [ ] Create layout shell (sidebar, header, content area)

**Auth pages**
- [ ] Build login page (beautiful, modern design)
- [ ] Build forgot password page
- [ ] Build password reset page
- [ ] Implement auth state management (Zustand)
- [ ] Implement protected route wrapper

**Dashboard**
- [ ] Build overview page with summary cards
- [ ] Build request chart (time-series)
- [ ] Build feature distribution chart
- [ ] Build recent errors list
- [ ] Build quick navigation cards

**Playground**
- [ ] Build playground page with tab navigation
- [ ] Build ChatTester component
- [ ] Build StreamingChatTester component
- [ ] Build FileUploadChat component
- [ ] Build ImageGenerator component
- [ ] Build ImageEditor component
- [ ] Build VideoGenerator component (with progress tracking)
- [ ] Build MusicGenerator component (with audio player)
- [ ] Build DeepResearch component (with progress + markdown result)
- [ ] Build GemsTester component
- [ ] Build ExtensionTester component
- [ ] Build TemporaryChat component
- [ ] Build HistoryReplay component
- [ ] Build CandidateSwitcher component
- [ ] Build shared controls: account selector, model selector, provider toggle, raw response viewer

**Accounts page**
- [ ] Build account list with health indicators
- [ ] Build add account wizard
- [ ] Build credential edit modal
- [ ] Build account health history chart
- [ ] Build validate/delete controls

**Models page**
- [ ] Build model table with search/filter
- [ ] Build capability badge components
- [ ] Build alias display
- [ ] Build refresh button

**Features (parity) page**
- [ ] Build parity matrix grid
- [ ] Build per-feature test buttons
- [ ] Build parity trend chart

**Logs page**
- [ ] Build log table with pagination
- [ ] Build filter bar
- [ ] Build request detail slide-out with event timeline
- [ ] Build replay button
- [ ] Build export buttons
- [ ] Build real-time log streaming toggle (WebSocket)

**Analytics page**
- [ ] Build all analytics panels (sections 11.1 through 11.9)
- [ ] Build time range selector
- [ ] Build drill-down navigation

**Admin page**
- [ ] Build user management table
- [ ] Build API key management
- [ ] Build server settings form
- [ ] Build audit log table
- [ ] Build package update status cards
- [ ] Build MCP config generator (outputs JSON for Claude Desktop, Cursor, etc.)

**Health page**
- [ ] Build public-facing status page
- [ ] Build per-component health indicators
- [ ] Build uptime chart

---

### Phase 8 — MCP server (Week 9-10)

**MCP implementation**
- [ ] Install FastMCP library
- [ ] Implement SSE transport handler at /mcp/sse
- [ ] Implement STDIO transport handler
- [ ] Register all tools (chat, image, video, music, research, gems, extensions, history, limits, jobs, health)
- [ ] Register resource definitions
- [ ] Implement MCP auth (gateway API key validation)
- [ ] Implement tenant routing (MCP requests go through gateway middleware)

**Integration docs**
- [ ] Write Claude Desktop configuration guide
- [ ] Write Claude Code configuration guide
- [ ] Write Cursor configuration guide
- [ ] Write Windsurf configuration guide
- [ ] Write generic MCP client guide
- [ ] Generate config JSON in admin GUI

**MCP analytics**
- [ ] Track tool invocations in analytics
- [ ] Track connected MCP clients
- [ ] Track SSE connection durations

**Tests**
- [ ] MCP tool invocation tests
- [ ] SSE transport tests
- [ ] STDIO transport tests
- [ ] Auth validation tests

---

### Phase 9 — Ops hardening (Week 10-11)

**Webhooks**
- [ ] Implement webhook registration CRUD
- [ ] Implement event dispatch system
- [ ] Support Slack + Discord webhook formats
- [ ] Implement delivery retry with backoff
- [ ] Implement webhook delivery log

**Security hardening**
- [ ] Audit all credential storage for encryption
- [ ] Implement master key rotation support
- [ ] Implement auto-expire for debug log payloads
- [ ] Review and harden all input validation
- [ ] Add CSRF protection for admin GUI
- [ ] Rate limit all public endpoints

**Docker production**
- [ ] Write Dockerfile.backend (multi-stage, slim)
- [ ] Write Dockerfile.frontend (nginx)
- [ ] Write Dockerfile.worker
- [ ] Write docker-compose.prod.yml (+ Nginx reverse proxy + Grafana + Prometheus)
- [ ] Write docker-compose.yml for local dev
- [ ] Health checks in compose files
- [ ] Volume configuration for persistent data

**Backup**
- [ ] Implement encrypted database backup command
- [ ] Implement encrypted config export/import
- [ ] Implement account credential export (encrypted archive)

**Tests**
- [ ] Full parity regression test suite
- [ ] Load testing with locust or similar
- [ ] Security scan (bandit)
- [ ] Dependency vulnerability scan

**Documentation**
- [ ] Write architecture.md
- [ ] Write api-mapping.md (OpenAI ↔ Gemini)
- [ ] Write parity-matrix.md
- [ ] Write auth-guide.md
- [ ] Write mcp-integration.md
- [ ] Write threat-model.md
- [ ] Write README.md with quickstart

---

## 22. Additional features (beyond original requirements)

| Feature | Priority | Description |
|---------|----------|-------------|
| RBAC | High | admin / operator / viewer / developer roles |
| Feature parity dashboard | High | Live matrix showing what works on each adapter |
| Account health monitor | High | State machine: healthy → degraded → unhealthy → recovering |
| Request replay | Medium | Re-run any historical request from GUI |
| Provider fallback toggle | Medium | Per-request: force specific adapter or auto |
| Request diff tool | Medium | Compare outputs from both adapters for same prompt |
| Webhook notifications | Medium | Job completion, error spikes, quota alerts, account failures |
| Tenant mode | Medium | Multi-team isolation if needed |
| Encrypted config export/import | Medium | Backup and restore all settings + credentials |
| Canary synthetic tests | Medium | Automated health probes every few minutes |
| Package update watcher | Medium | Monitor upstream PyPI versions + auto-refresh models |
| Manual capability override | Low | Admin can force-enable/disable features per account |
| Cost proxy dashboard | Low | Track "what this would cost" as equivalent API calls |
| Prompt template library | Low | Store, version, share reusable prompts |
| Conversation fork/branch | Low | Explore different paths from same point |
| Plugin system | Low | Community-contributed feature extensions |

---

## 23. Acceptance criteria summary

The project is considered complete when:

1. All OpenAI-compatible endpoints work with standard OpenAI SDK clients
2. All native endpoints expose every feature from both upstream libraries
3. SSE streaming works for chat and job progress
4. Multiple Gemini accounts can be linked via GUI, CLI, and terminal paste
5. Cookie auth, API key auth, and browser import all functional
6. All request are logged with structured metadata
7. Analytics dashboard shows all 9 panel types with real data
8. Swagger UI documents all endpoints with examples
9. Web GUI playground can test every feature from browser
10. MCP server exposes all features as tools, usable from Claude Desktop
11. Password reset works from terminal CLI
12. dev-start.sh / dev-stop.sh manage full dev environment
13. Model aliases resolve correctly and auto-update on discovery
14. Feature parity dashboard reflects real test results
15. Admin RBAC restricts access appropriately
16. All credentials encrypted at rest
17. Docker Compose spins up complete production stack