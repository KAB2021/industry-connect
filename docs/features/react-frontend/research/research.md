---
feature: react-frontend
type: research
created: 2026-03-04T00:00:00Z
---

# Research: React Frontend

## Relevant Code

### API Endpoints

- `app/routers/ingestion.py:17-59` — `POST /upload/csv`. Multipart form field `file` (UploadFile). Returns `list[OperationalRecordRead]` on 201. Returns `ErrorResponse` on 422. Raises `HTTPException(413, detail="File exceeds maximum upload size")` when file > `MAX_UPLOAD_BYTES`. Note: 413 returns `{"detail": "..."}`, NOT the `ErrorResponse` shape.
- `app/routers/webhook.py:14-37` — `POST /webhook`. JSON body `WebhookPayload`. Returns `OperationalRecordRead` on 201. Checks `Content-Length` header against `MAX_UPLOAD_BYTES`.
- `app/routers/records.py:11-17` — `GET /records?limit=100&offset=0`. Returns `list[OperationalRecordRead]`. Limit: 1–1000 (default 100). Offset: >= 0. No server-side filtering or sorting — returns in DB insertion order.
- `app/routers/analysis.py:18-52` — `POST /analyse`. No request body. Returns `list[AnalysisResultRead]` on 200. Returns `[]` when no unanalysed records exist. Raises `HTTPException(413, detail="Input data too large for analysis")` when serialised records > `MAX_UPLOAD_BYTES`. Note: 413 returns `{"detail": "..."}`.
- `app/main.py:51-53` — `GET /health`. Returns `{"status": "ok"}`.

### Data Schemas (Wire Format)

- `app/schemas/operational_record.py:7-17` — `OperationalRecordRead`: `id` (UUID), `source` (str: "csv"|"webhook"|"poll"), `timestamp` (datetime), `entity_id` (str), `metric_name` (str), `metric_value` (float), `analysed` (bool), `ingested_at` (datetime).
- `app/schemas/analysis_result.py:8-19` — `AnalysisResultRead`: `id` (UUID), `record_ids` (list[str] — UUID strings), `summary` (str), `anomalies` (list[dict]), `prompt` (str), `response_raw` (str), `prompt_tokens` (int|None), `completion_tokens` (int|None), `created_at` (datetime).
- `app/schemas/errors.py:4-11` — `ErrorResponse`: `{"errors": [{"row": int, "field": str, "message": str}]}`. Used by `POST /upload/csv` 422 and the global `RequestValidationError` handler.

### Anomaly Object Shape (Enforced by OpenAI Structured Output)

- `app/services/analysis.py:36-50` — Each anomaly dict has exactly: `record_id` (str), `metric_name` (str), `metric_value` (number), `explanation` (str). `additionalProperties: false` enforced — shape is guaranteed stable.

### Analysis Lifecycle

- `app/services/analysis.py:150-279` — `run_analysis()` queries all records where `analysed == false`, runs single-pass or map-reduce via OpenAI, persists `AnalysisResult` rows, marks records `analysed = true`, commits. In map-reduce mode, one `AnalysisResult` is created per chunk plus one final reduce result — all returned in the list.
- The `record_ids` field on `AnalysisResult` links results back to the `OperationalRecord` rows they cover. Chunk results reference only their chunk's records; the final reduce result references all records.

### Error Response Shapes

Two distinct 4xx shapes exist:
1. **422 errors** — `{"errors": [{"row": int, "field": str, "message": str}]}` (ErrorResponse schema)
2. **413 errors** — `{"detail": "..."}` (FastAPI HTTPException default)

The frontend must handle both shapes differently.

### CORS Configuration

- **None exists.** No `CORSMiddleware`, no `allow_origins`, no CORS-related env vars anywhere in the codebase. This is a **hard prerequisite** — any browser-based frontend on a different origin will be blocked by same-origin policy until CORS middleware is added.

### Docker Setup

- `docker-compose.yml:1-34` — Two services: `postgres` (port 5433:5432) and `app` (port 8000:8000). Backend accessible at `http://localhost:8000` from the host.
- `Dockerfile:1-24` — `python:3.12-slim`, `COPY . .` at line 16 copies entire project root into image. **No `.dockerignore` exists.** A `frontend/` directory with `node_modules/` (200–500MB) would be copied into the backend image, causing major bloat. A `.dockerignore` must be created before adding the frontend.

### Environment Variables

- `app/config.py` — `DATABASE_URL`, `TEST_DATABASE_URL`, `OPENAI_API_KEY` (required). `OPENAI_MODEL` (default "gpt-4o-mini"), `POLL_INTERVAL_SECONDS` (default 60), `POLL_SOURCE_URL` (default ""), `MAX_UPLOAD_BYTES` (default 10485760 = 10MB), `TOKEN_THRESHOLD` (default 4000).
- No auth env vars. The API is completely open — no tokens, sessions, or API keys required for any endpoint.

### Auto-Generated Docs

- FastAPI serves Swagger UI at `/docs` and OpenAPI schema at `/openapi.json`. Available at `http://localhost:8000/docs`.

## Patterns & Standards

- No coding standards documentation exists in the project (`docs/coding_standards/` does not exist).
- The backend uses Pydantic v2 (`model_config = ConfigDict(from_attributes=True)`) for all schemas.
- All datetime fields are timezone-aware (UTC).
- UUID fields are `uuid.UUID` in Python, serialised as strings in JSON.
- The project uses SQLAlchemy ORM with Alembic migrations.
- FastAPI dependency injection via `Depends(get_db)` for database sessions.

## External Findings

### Scaffolding: Vite + React + TypeScript

- `create-vite` with the `react-ts` template remains the standard scaffolding approach. Command: `npm create vite@latest frontend -- --template react-ts`.
- Vite 6.x is current (2025/2026). Fast HMR, native ESM dev server.

### Tailwind CSS v4

- Released early 2025. Major changes from v3: no `tailwind.config.js` by default, no PostCSS/Autoprefixer needed, dedicated `@tailwindcss/vite` plugin, CSS `@import` replaces `@tailwind` directives.
- Custom design tokens (colors, fonts) can still be configured via CSS `@theme` blocks — no config file needed for simple customisation.
- Sources: [Tailwind CSS docs](https://tailwindcss.com/docs), [Vite setup guide](https://dev.to/geane_ramos/how-to-setup-your-vite-project-with-react-typescript-and-tailwindcss-v4-2bkm)

### Client-Side Routing

**React Router v7:**
- Mature, widely adopted. Dual-mode: SPA library mode and framework mode. In SPA mode (what we'd use), type safety is limited compared to TanStack Router.
- Simpler API for basic use cases. Well-documented.

**TanStack Router:**
- TypeScript-first with automatic type inference for routes, params, and search queries. Catches routing errors at compile time.
- Steeper initial setup but better long-term safety for apps that grow.
- Sources: [TanStack comparison](https://tanstack.com/router/latest/docs/framework/react/comparison), [Better Stack comparison](https://betterstack.com/community/comparisons/tanstack-router-vs-react-router/)

### Data Fetching

**TanStack Query (React Query):**
- Built-in `refetchInterval` for auto-polling — directly maps to the 30s polling requirement. Handles caching, deduplication, loading/error states, and stale-while-revalidate out of the box.
- `useMutation` for POST requests (upload, analyse) with built-in loading/error/success state management.
- Eliminates the need for manual `useState`/`useEffect` boilerplate for every API call.
- Sources: [TanStack Query docs](https://tanstack.com/query/v4/docs/framework/react/examples/auto-refetching), [Usage guide](https://blog.openreplay.com/tanstack-query-smarter-data-fetching-react/)

**Manual useState + useEffect:**
- Zero dependencies. Full control. But requires manual handling of loading, error, caching, race conditions, and cleanup for every endpoint. Fragile at scale.

### HTTP Client

**fetch API (native):**
- Zero bundle cost. Supports FormData for file uploads. No progress tracking without ReadableStream (complex). Sufficient for this project since upload progress is not in the spec.

**Axios:**
- ~35kb added bundle. Built-in interceptors, progress tracking, request cancellation. Overkill for a project that doesn't require upload progress.
- Sources: [LogRocket comparison](https://blog.logrocket.com/axios-vs-fetch-2025/), [OpenReplay guide](https://blog.openreplay.com/axios-vs-fetch-api-guide-http-requests-2025/)

### Table Component

**TanStack Table:**
- Headless (~15kb). Powerful sorting, filtering, pagination hooks. But it's headless — you build all UI markup yourself.
- Potential conflict: backend does server-side pagination (limit/offset), and TanStack Table's client-side pagination could confuse the model. Would need to wire server-side pagination into TanStack Table's manual pagination mode.

**Manual table (map + sort/filter functions):**
- Simpler for 7 columns with basic sort/filter. No library overhead. Client-side sort/filter over loaded records is straightforward with Array.sort() and Array.filter().
- Sources: [TanStack Table docs](https://tanstack.com/table/latest), [LogRocket guide](https://blog.logrocket.com/tanstack-table-formerly-react-table/)

## Risks

1. **CORS is a hard blocker.** No CORS middleware exists. The backend must be modified before any browser-based frontend can call the API from a different origin. This is a prerequisite, not a configuration task — it requires adding `CORSMiddleware` to `app/main.py` and ideally a `CORS_ALLOWED_ORIGINS` env var to `app/config.py`. Likelihood: certain. Impact: total blocker. Mitigation: add CORS as the first task.

2. **Docker image bloat from `COPY . .` without `.dockerignore`.** A `frontend/` directory with `node_modules/` (200–500MB) will be copied into the backend Docker image. This could cause CI build failures or excessive image sizes. Likelihood: certain (once frontend exists). Impact: high. Mitigation: create `.dockerignore` excluding `frontend/node_modules/`, `frontend/dist/`, etc.

3. **413 error shape differs from 422 error shape.** 413 returns `{"detail": "..."}` (FastAPI default) while 422 returns `{"errors": [...]}` (custom ErrorResponse). The frontend error handling must detect the status code and parse the appropriate shape. Likelihood: certain. Impact: medium (incorrect error display). Mitigation: status-code-based error parsing in the API client layer.

4. **`prompt` and `response_raw` fields in `AnalysisResultRead`.** These contain the full LLM prompt (including all record data) and raw LLM response. Exposing these to the frontend is a data consideration — they may contain all operational record data in string form. Not a security risk (no auth exists and data is already accessible via `/records`), but the fields could be large and slow down rendering if displayed naively. Mitigation: collapse/hide these fields by default in the UI.

5. **No API versioning.** Endpoints have no `/v1/` prefix. Backend changes could break the frontend silently. Likelihood: low (portfolio project). Impact: medium. Mitigation: none needed for current scope.

## Answers to Open Questions

**Q: Should the frontend be added to the existing `docker-compose.yml` as a separate service, or run standalone outside Docker during development?**

Evidence gathered:
- The backend runs in Docker on port 8000. No CORS middleware exists.
- Running the frontend standalone on `localhost:5173` (Vite default) while the backend is on `localhost:8000` will fail immediately due to CORS — different ports = different origins.
- After CORS middleware is added, standalone dev works fine: Vite's dev server proxy (`server.proxy` in `vite.config.ts`) can forward `/api` calls to `localhost:8000`, avoiding CORS entirely during development.
- For production/Docker deployment, a separate `frontend` service in `docker-compose.yml` using a multi-stage build (Node build stage → nginx serve stage) is the standard approach. This keeps the backend image clean.
- Vite HMR inside Docker on macOS has known performance issues with volume mounts (inotify limitations). Development is faster running Vite natively on the host.

**Recommendation:** Run standalone during development (with Vite proxy or CORS enabled). Add as a Docker service for production builds. This is a genuine multi-option decision — documented in `decisions.md`.
