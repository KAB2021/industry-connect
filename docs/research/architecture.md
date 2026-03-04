---
project: IndustryConnect
created: 2026-03-04T00:00:00Z
---

# Architecture

## Overview

IndustryConnect is a synchronous FastAPI application backed by PostgreSQL. It exposes three ingestion paths (CSV upload, webhook, background poller), a unified records retrieval endpoint, and an LLM analysis endpoint. All components run as a single `docker-compose up` command.

```
┌─────────────────────────────────────────────────┐
│                  FastAPI App                    │
│                                                 │
│  POST /upload/csv   POST /webhook   (poller)    │
│        │                 │              │        │
│        └────────┬─────────┘              │        │
│                 ▼                        │        │
│         csv_parser.py              poller.py     │
│                 │                        │        │
│                 └──────────┬─────────────┘        │
│                            ▼                      │
│                  OperationalRecord ORM            │
│                            │                      │
│                       PostgreSQL                  │
│                            │                      │
│                   GET /records                    │
│                            │                      │
│                   POST /analyse                  │
│                            │                      │
│                    analysis.py                    │
│                  (single-pass / map-reduce)       │
│                            │                      │
│                       OpenAI API                  │
│                            │                      │
│                  AnalysisResult ORM               │
│                       PostgreSQL                  │
└─────────────────────────────────────────────────┘
```

## Technology Choices

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Web framework | FastAPI | Async-capable, built-in OpenAPI docs, Pydantic integration |
| ORM | SQLAlchemy (sync) with psycopg2 | Predictable transaction semantics; avoids mixing sync DB I/O with async complexity. Async SQLAlchemy/asyncpg was considered but deferred |
| Database | PostgreSQL | JSON column support for `anomalies` and `record_ids`; `gen_random_uuid()` server-side UUID generation |
| Migrations | Alembic | Standard SQLAlchemy companion; supports `autogenerate` from ORM models |
| LLM provider | OpenAI (gpt-4o-mini default) | Configurable via `OPENAI_MODEL` env var; structured output via `json_schema` response format enforces the `summary`/`anomalies` contract |
| LLM client mocking | `respx` | Intercepts `httpx` requests at the transport layer; no vendor-specific test plugin required |
| Background scheduling | `asyncio.create_task` in FastAPI lifespan | No APScheduler dependency; sufficient for a single-interval poller at portfolio scope |
| Settings | `pydantic-settings` | `.env` parsing with type coercion; single `Settings` instance imported as `settings` |
| Linting / typing | ruff + mypy | Enforced in CI |
| Containerisation | Docker Compose | Single-command startup; no hardcoded secrets; credentials injected via `.env` |

## Directory Structure

```
frontend/
  package.json               # React 19, React Router v7, TanStack Query v5, Tailwind CSS v4
  vite.config.ts             # Build config + dev proxy to localhost:8000
  Dockerfile                 # Multi-stage: Node 20 Alpine (build) → nginx Alpine (serve)
  nginx.conf                 # SPA fallback + reverse proxy for API paths
  src/
    main.tsx                 # QueryClientProvider + RouterProvider
    App.tsx                  # createBrowserRouter — 4 routes
    layouts/AppLayout.tsx    # Persistent top nav bar
    pages/                   # DashboardPage, RecordsPage, UploadPage, AnalysisPage
    components/              # RecordsTable, AnalysisResultCard
    api/types.ts             # TypeScript interfaces for all API shapes + ApiError
    api/client.ts            # fetch wrapper with status-code-based error parsing
    hooks/                   # useRecords, useUploadCSV, useAnalysis
app/
  config.py                  # Centralised settings (pydantic-settings)
  main.py                    # App factory, lifespan, global exception handler
  db/
    base.py                  # Declarative Base
    session.py               # SessionLocal, get_db dependency
  models/
    operational_record.py    # OperationalRecord ORM model
    analysis_result.py       # AnalysisResult ORM model
  schemas/
    operational_record.py    # Pydantic read/write schemas
    analysis_result.py       # Pydantic read schema
    errors.py                # Shared ErrorResponse / RowError shapes
  routers/
    ingestion.py             # POST /upload/csv
    webhook.py               # POST /webhook
    records.py               # GET /records
    analysis.py              # POST /analyse
  services/
    csv_parser.py            # Column resolution (alias/explicit mapping) + row-level CSV validation
    analysis.py              # run_analysis(): single-pass and map-reduce logic
    chunking.py              # Token-bounded record chunking
    token_counter.py         # tiktoken wrapper with lru_cache
    poller.py                # Async polling loop
alembic/                     # Database migrations
tests/
  conftest.py                # Test DB session; DELETE-based isolation
  test_*.py                  # 104 tests across all layers
docker-compose.yml
Dockerfile
.env.example
```

## Request Lifecycle

### CSV Upload (`POST /upload/csv`)

1. Router reads the uploaded file bytes and checks `len(content)` against `MAX_UPLOAD_BYTES`; returns HTTP 413 with a descriptive message if exceeded.
2. If an optional `column_mapping` form field is provided, the router parses it as JSON and validates it is a `dict[str, str]`; returns HTTP 422 on malformed input.
3. `csv_parser.resolve_columns()` resolves each required column through a three-step lookup: explicit mapping → canonical match → alias match (all case-insensitive). Returns a rename map, `mappings_applied` audit dict, and any header-level errors (ambiguous, unresolvable, or absent columns).
4. `csv_parser.parse_and_validate()` renames row keys via the rename map, then validates each row; invalid rows accumulate as `CSVRowError` objects.
5. If any errors exist, returns HTTP 422 `{"errors": [...]}`.
6. Valid rows are inserted as `OperationalRecord` instances with `source="csv"`, `analysed=False`.
7. Session is committed; HTTP 201 returned with `CSVUploadResponse` containing `records` and `mappings_applied`.

### Webhook (`POST /webhook`)

1. FastAPI validates the request body against `WebhookPayload` Pydantic schema.
2. On validation failure, the global `RequestValidationError` handler in `main.py` converts the error to `{"errors": [{"row": 0, "field": str, "message": str}]}` and returns HTTP 422.
3. Valid payload is inserted as `OperationalRecord` with `source="webhook"`.

### Background Poller

1. `asyncio.create_task(run_poller(SessionLocal))` is called in the FastAPI lifespan context manager.
2. The poller sleeps for `POLL_INTERVAL_SECONDS`, fetches from `POLL_SOURCE_URL`, validates timestamps with `datetime.fromisoformat()`, and persists records with `source="poll"`.
3. The task is cancelled cleanly on application shutdown.

### Analysis (`POST /analyse`)

1. Router calls `run_analysis(db)`, passing the injected `Session` directly.
2. All `OperationalRecord` rows where `analysed=False` are loaded.
3. If total token count (via `token_counter.py`) is within `TOKEN_THRESHOLD`: single OpenAI call; one `AnalysisResult` persisted.
4. If over threshold: `chunking.py` splits records into token-bounded chunks; each chunk is summarised (map phase); chunk summaries are recursively combined up to `_MAX_REDUCE_ITERATIONS = 5` times (reduce phase); final combined result is persisted.
5. All processed records are marked `analysed=True`; session is committed.

## Data Models

### OperationalRecord

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Python default `uuid.uuid4`; server default `gen_random_uuid()` |
| `source` | String (NOT NULL) | `csv`, `webhook`, or `poll` |
| `timestamp` | DateTime (tz-aware, NOT NULL) | From the ingested payload |
| `entity_id` | String (NOT NULL) | |
| `metric_name` | String (NOT NULL) | |
| `metric_value` | Float (NOT NULL) | |
| `analysed` | Boolean (NOT NULL) | Default `False` |
| `ingested_at` | DateTime (tz-aware, NOT NULL) | Server default `now()` |

### AnalysisResult

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | Server default `gen_random_uuid()` |
| `record_ids` | JSON (NOT NULL) | Array of OperationalRecord UUID strings |
| `summary` | Text (NOT NULL) | Plain-English summary from LLM |
| `anomalies` | JSON (NOT NULL) | Array of anomaly objects from LLM |
| `prompt` | Text (NOT NULL) | Full rendered prompt as submitted |
| `response_raw` | Text (NOT NULL) | Raw LLM response text |
| `prompt_tokens` | Integer (nullable) | From OpenAI usage metadata |
| `completion_tokens` | Integer (nullable) | From OpenAI usage metadata |
| `created_at` | DateTime (tz-aware, NOT NULL) | Server default `now()` |

## Frontend Architecture

### Development

Vite's `server.proxy` in `vite.config.ts` forwards API requests from `localhost:5173` to `localhost:8000`. The browser sees same-origin requests, so no CORS headers are needed during development.

### Production (Docker)

The frontend container runs nginx on port 80 (mapped to host port 3000). nginx proxies `/upload`, `/webhook`, `/records`, `/analyse`, `/health`, `/docs`, and `/openapi.json` to `http://app:8000` on the Docker network. Static assets are served from `dist/`; unmatched routes fall back to `index.html` for SPA routing. CORS middleware on the backend permits requests from the frontend origin via `CORS_ALLOWED_ORIGINS`.

### Docker Service Topology

```
postgres:5432 ← app:8000 ← frontend:80 (host :3000)
     ▲              ▲            ▲
  (healthcheck)  depends_on   depends_on
                 postgres        app
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated list of origins allowed by CORS middleware |
| `VITE_API_BASE_URL` | `""` (build-time) | Backend API base URL; empty uses Vite proxy or nginx proxy |
| `VITE_POLL_INTERVAL_MS` | `30000` (build-time) | Records auto-poll interval in milliseconds |
| `DATABASE_URL` | (required) | SQLAlchemy connection string for the application database |
| `TEST_DATABASE_URL` | (required) | Separate database used during test runs |
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name passed to OpenAI chat completions |
| `POLL_INTERVAL_SECONDS` | `60` | Seconds between poller fetch cycles |
| `POLL_SOURCE_URL` | `""` | URL the poller fetches from |
| `MAX_UPLOAD_BYTES` | `10485760` | Maximum accepted CSV file size (10 MB) |
| `TOKEN_THRESHOLD` | `4000` | Token count above which map-reduce is used |
| `POSTGRES_USER` | (required for Compose) | PostgreSQL username (used by docker-compose) |
| `POSTGRES_PASSWORD` | (required for Compose) | PostgreSQL password (used by docker-compose) |
| `POSTGRES_DB` | (required for Compose) | PostgreSQL database name (used by docker-compose) |

## Testing Strategy

- **Framework**: pytest with FastAPI `TestClient` for endpoint tests.
- **Database**: A separate `TEST_DATABASE_URL` database is used; no test containers. Tables are created via `Base.metadata.create_all` in the session fixture.
- **Isolation**: Each test cleans up via `DELETE FROM` on all tables. Transaction rollback was considered but removed to ensure services that open their own sessions see a consistent state.
- **LLM mocking**: `respx` intercepts outbound `httpx` requests to the OpenAI API; no real API calls are made during tests.
- **Coverage areas**: CSV ingestion (valid + invalid paths), webhook ingestion (valid + invalid paths, body shape assertion), poller (full cycle producing a persisted record), analysis result persistence (all fields asserted non-null), `analysed` flag lifecycle, `GET /records` retrieval, integration test covering all three sources in one session.

## Known Limitations and Natural Next Steps

- **No authentication**: All endpoints are open. Adding OAuth2 or API key middleware is the natural next production step.
- **Synchronous DB in async context**: The poller runs sync SQLAlchemy writes inside an `async def`, which blocks the event loop. Acceptable for single-poller portfolio scope; a production system should use `asyncio.to_thread` or switch to async SQLAlchemy.
- **Single LLM provider**: Provider is fixed at startup via env var. Runtime provider switching is out of scope.
- **Poller interval is startup-only**: The interval cannot be changed via API; a restart is required.
- **`prompt_tokens` and `completion_tokens` are nullable**: OpenAI usage metadata is not guaranteed by the API contract; these fields are intentionally nullable while all other `AnalysisResult` fields are `NOT NULL`.
- **Dashboard stats capped at 100 records**: `DashboardPage` calls `useRecords(100)`, so total and pending counts under-count for larger datasets.
- **Dashboard analysis placeholder**: "Most Recent Analysis Result" section is rendered but not wired to session data.
- **Session-only analysis history**: Results are held in React component state and lost on page refresh; no backend endpoint exists for historical results.
