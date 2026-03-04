# Changelog

All notable changes to this project are documented here.

---

## [Unreleased]

### Fixed — React Frontend Post-Completion (feat-e87c6de9)

**Vite proxy route collision**
- Consolidated per-route proxy rules (`/records`, `/upload`, etc.) into a single `/api` prefix with path rewrite. Previously, navigating to `/records` in the browser returned raw JSON from the backend instead of the React SPA.
- `VITE_API_BASE_URL` set to `/api`; `BASE_URL` fallback changed from `??` to `||` to handle empty string env values.

**Persisted analysis results**
- Added `GET /analyse` endpoint with `limit`/`offset` pagination (ordered by `created_at desc`). Analysis results now survive page refreshes — previously session-only.
- Dashboard "Most Recent Analysis Result" section now displays the actual latest result (was a static placeholder).
- Analysis page fetches persisted results from `GET /analyse` and invalidates the cache after triggering new analysis.
- Added error states for failed analysis result fetches on both Dashboard and Analysis pages.

### Added — Smart CSV Column Mapping (feat-8f9dc161)

`POST /upload/csv` now accepts CSVs with non-canonical column names and resolves them automatically via alias matching or an optional explicit `column_mapping` parameter. All 10 success criteria pass; 104 tests total.

**Column resolution**
- Fixed alias table: `site_id`/`station_id`/`asset_id` → `entity_id`; `metric`/`measurement`/`kpi` → `metric_name`; `value`/`reading`/`val` → `metric_value`; `timestamp` has no aliases
- Three-step per-field lookup: explicit mapping → canonical match → alias match (all case-insensitive)
- HTTP 422 on unresolvable columns, absent explicit-mapping targets, or ambiguous multi-column resolution
- Extra columns silently discarded

**Response shape change**
- `POST /upload/csv` now returns `{"records": [...], "mappings_applied": {...}}` (`CSVUploadResponse`) instead of a bare JSON array
- `mappings_applied` always has 4 keys mapping canonical name → source column name (identity entries when columns match directly)
- Optional `column_mapping` form field accepts a JSON string for explicit column overrides

### Added — React Frontend (feat-e87c6de9)

A React 19 SPA providing a browser-based interface for all IndustryConnect backend capabilities. TypeScript strict; Vite 7 build; Tailwind CSS v4; 15/16 success criteria pass (1 partial).

**Views**
- Dashboard — total records count, pending-analysis count, and analysis result placeholder
- Records — paginated table (`GET /records` limit/offset) with client-side filter by source and sort by timestamp/ingested_at; auto-polls at `VITE_POLL_INTERVAL_MS` (default 30s) with manual refresh
- Upload — CSV file form targeting `POST /upload/csv`; displays ingested count on 201, row-level error table on 422, size-exceeded message on 413
- Analysis — trigger button calling `POST /analyse`; disabled with "No records pending analysis" when no unanalysed records; session-scoped result history in reverse chronological order; 413 error handling

**Frontend infrastructure**
- React Router v7 (client-side routing), TanStack Query v5 (data fetching + auto-polling + mutations), native `fetch` wrapper with typed error handling
- Vite dev server with `server.proxy` forwarding API paths to `localhost:8000`
- Multi-stage Dockerfile (Node 20 Alpine → nginx Alpine); nginx reverse-proxies API paths to `app:8000` with SPA `try_files` fallback
- `frontend` service added to `docker-compose.yml` on host port 3000

**Backend additions**
- `CORSMiddleware` added to `app/main.py`; origins configurable via `CORS_ALLOWED_ORIGINS` (comma-separated, whitespace-stripped)
- `.dockerignore` created to exclude `frontend/node_modules`, `frontend/dist`, `.git`, `__pycache__`, `.env`

**Post-review fixes**
- `SortIndicator` component hoisted to module scope (was inside component body)
- `setState` in `useEffect` moved to `useMutation` `onSuccess` callback
- Unsafe `as ApiError` casts replaced with `instanceof` checks
- CORS origin split now strips whitespace
- `.env` added to `frontend/.gitignore`
- `restart: unless-stopped` added to frontend Docker service

### Added — IndustryConnect (feat-73dd2524)

A FastAPI backend for ingesting, storing, and analysing operational data. 93 tests pass; ruff and mypy clean.

**Ingestion**
- `POST /upload/csv` — multipart CSV upload; row-level validation returns `{"errors": [...]}` on invalid rows; rejects files over `MAX_UPLOAD_BYTES` (default 10 MB) with HTTP 413 and a descriptive message
- `POST /webhook` — single-record JSON receiver; validation errors normalised to the same `{"errors": [...]}` response shape via a global `RequestValidationError` handler
- Background poller — async task started in FastAPI lifespan; fetches from a configurable mock HTTP server on `POLL_INTERVAL_SECONDS` interval; timestamps validated with `datetime.fromisoformat()` before persistence

**Storage**
- `OperationalRecord` PostgreSQL table — normalised schema used by all three ingestion paths; `source` distinguishes `csv | webhook | poll`
- `AnalysisResult` PostgreSQL table — stores the full rendered prompt, raw LLM response, token counts, anomalies array, and references to the analysed record IDs; all text fields are `NOT NULL` at the DB level
- Alembic migrations for both tables; `NOT NULL` constraint on `AnalysisResult` text fields added in a post-review migration

**Analysis**
- `POST /analyse` — processes all records where `analysed=false`, marks them `true` on success, and persists an `AnalysisResult`
- Single-pass mode for inputs within `TOKEN_THRESHOLD`; map-reduce mode (max 5 reduce iterations) for larger inputs
- Model configurable via `OPENAI_MODEL` env var (default `gpt-4o-mini`); structured JSON output via OpenAI's `json_schema` response format

**Records**
- `GET /records` — retrieves all ingested records with `limit` (default 100, max 1000) and `offset` pagination

**Operations**
- `docker-compose up` brings the full stack (app + PostgreSQL) to a ready state; no hardcoded secrets; all credentials injected via `.env`
- `.env.example` documents all required variables
- GitHub Actions CI runs ruff, mypy, and pytest on every push

**Post-review fixes applied before release**
- Webhook 422 body format corrected (was FastAPI default `{"detail": [...]}`)
- CSV 413 response now includes a descriptive error body
- `AnalysisResult` nullable fields hardened to `NOT NULL`
- Double-session architecture in analysis router removed; `Session` passed directly
- Hardcoded DB password in `docker-compose.yml` replaced with env var substitution
- Reduce loop bounded to `_MAX_REDUCE_ITERATIONS = 5`
- Poller timestamp parsing made explicit
- `tiktoken` encoding cached with `lru_cache`
- Test isolation simplified to `DELETE`-only cleanup
