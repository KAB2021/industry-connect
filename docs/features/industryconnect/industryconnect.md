---
id: feat-73dd2524
title: IndustryConnect
status: complete
created: 2026-03-04T00:00:00Z
---

# IndustryConnect

## Overview

IndustryConnect exposes a FastAPI backend that accepts operational data through three distinct ingestion paths: a CSV file upload endpoint, a webhook receiver endpoint, and a background polling task that fetches from a mock HTTP server defined within the project. Regardless of which path data enters through, it is normalised into a consistent `OperationalRecord` structure and persisted in PostgreSQL. A consumer of the API can ingest data from any of these three sources and then retrieve those records through a unified interface.

The `OperationalRecord` schema contains the following fields: `id` (UUID, server-assigned), `source` (enum: `csv` | `webhook` | `poll`), `timestamp` (ISO 8601, UTC), `entity_id` (string), `metric_name` (string), `metric_value` (float), `analysed` (boolean, default `false`), and `ingested_at` (ISO 8601, UTC, server-assigned).

Once data is ingested, the API exposes an analysis endpoint that processes only records where `analysed` is `false`. The endpoint sends these un-analysed records to an LLM and returns a plain-English summary along with any flagged anomalies — unusual values or patterns — explained in natural language. Upon completion, the processed records are marked as `analysed: true`, and the LLM response is persisted in a separate `AnalysisResult` table linked back to the records it covers. The `AnalysisResult` schema contains: `id` (UUID), `record_ids` (array of UUID references to the `OperationalRecord` entries included), `summary` (string), `anomalies` (JSON array), `prompt` (the full rendered prompt string as submitted to the LLM API, verbatim), `response_raw` (the raw LLM response text), `prompt_tokens` (int), `completion_tokens` (int), and `created_at` (ISO 8601, UTC).

For large inputs that exceed a configurable token threshold, the endpoint uses a map-reduce summarisation strategy: it splits the records into chunks, summarises each chunk individually using a cost-efficient model (e.g. GPT-4.1 mini), then combines the chunk summaries into a final summary in a second LLM call. Inputs exceeding a configurable maximum file size (default 10 MB, set via environment variable) are rejected with HTTP 413 before any LLM call is made.

The entire stack runs as a single `docker-compose up` command with no manual setup required beyond providing API credentials via a `.env` file at the project root. A `.env.example` file is committed to the repository documenting all required variables. The background poller's interval is configured via environment variable at startup.

The project is self-documenting via FastAPI's built-in `/docs` interface, which exposes all endpoints, request schemas, and response shapes. A README provides architecture context, setup instructions, and design rationale for a developer audience evaluating the codebase.

## Success Criteria

- [x] A CSV file posted to the upload endpoint is parsed and each valid row persisted as an `OperationalRecord` with `analysed: false` in PostgreSQL.
- [x] Records ingested via any path are retrievable via `GET /records` in the same request cycle without manual intervention.
- [x] The background poller fetches from the mock HTTP server on a configurable interval (set via environment variable at startup). After one polling cycle completes — verified by waiting for the configured interval plus a 5-second buffer — at least one `OperationalRecord` with `source: poll` is retrievable via `GET /records`. The mock server's response schema is documented in the project.
- [x] All persisted records conform to the `OperationalRecord` schema defined in the Overview, regardless of ingestion path.
- [x] The analysis endpoint processes only records where `analysed` is `false`. After a successful analysis call, those records are marked `analysed: true` and are not re-processed by subsequent analysis calls.
- [x] Each analysis call persists an `AnalysisResult` row containing: the full rendered prompt string (verbatim), the raw LLM response text, prompt token count, completion token count, a summary string, an anomalies array, and references to the `OperationalRecord` IDs that were included.
- [x] When the input to the analysis endpoint exceeds the configurable token threshold, the endpoint splits records into chunks, summarises each chunk individually, and produces a final combined summary from the chunk summaries (map-reduce strategy).
- [x] Inputs exceeding the configurable maximum file size (default 10 MB) are rejected with HTTP 413 and a descriptive error message before any LLM call is made.
- [x] Posting a CSV with one or more invalid rows returns HTTP 422 with a response body of the shape `{"errors": [{"row": int, "field": str, "message": str}]}`, one entry per invalid row.
- [x] Posting a malformed or schema-invalid webhook payload returns HTTP 422 with a response body of the same shape: `{"errors": [{"row": int, "field": str, "message": str}]}`, where `row` is 0 for single-object payloads.
- [x] Given a valid `.env` file present at the project root, `docker-compose up` brings the full stack to a ready state with no additional manual steps.
- [x] The test suite covers: CSV ingestion (valid and at least one invalid/error path), webhook ingestion (valid and at least one invalid/error path), poll ingestion (at least one cycle producing a persisted record), analysis result persistence (asserting all `AnalysisResult` fields are present and non-null), the `analysed` flag toggle lifecycle, and `GET /records` retrieval.

## Scope

**IN:**
- CSV file upload ingestion endpoint
- Webhook receiver ingestion endpoint
- Background polling task targeting a mock HTTP server defined within the project (interval set via environment variable at startup)
- Normalisation of all ingestion paths into the `OperationalRecord` schema with `analysed` tracking flag
- PostgreSQL persistence
- `GET /records` unified retrieval endpoint
- LLM analysis endpoint that processes only un-analysed records
- `AnalysisResult` table storing LLM responses, summaries, anomalies, prompt, token counts, and record references
- Map-reduce chunked summarisation for large inputs with a file size ceiling rejection (default 10 MB)
- Analysis log persistence including prompt, response, and token counts
- Error responses with the defined schema for CSV and webhook ingestion
- `/docs` auto-documentation
- `docker-compose` single-command startup
- `.env`-based credential configuration with `.env.example` committed

**OUT:**
- Authentication or authorisation on any endpoint (portfolio scope — natural next step for production)
- Pagination or filtering on `GET /records` (defer to keep initial scope focused)
- Streaming LLM responses (synchronous response only)
- Storage of original uploaded binary files or raw webhook JSON bodies; normalised field values derived from ingested data may appear in LLM prompts
- Multiple simultaneous LLM provider selection at runtime (provider is set via environment variable)
- Runtime-configurable polling interval via API (startup-only configuration is sufficient for portfolio scope)
- Any frontend or UI beyond `/docs`

## Implementation Notes

### Key Architectural Files and Their Roles

| File | Role |
|------|------|
| `app/main.py` | FastAPI application factory, lifespan handler (starts background poller via `asyncio.create_task`), global `RequestValidationError` handler that converts validation errors to the spec's `{"errors": [...]}` format |
| `app/config.py` | Centralised settings via `pydantic-settings`; reads all configuration from `.env` including `DATABASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `POLL_INTERVAL_SECONDS`, `MAX_UPLOAD_BYTES`, and `TOKEN_THRESHOLD` |
| `app/db/base.py` | Declarative `Base` shared by all ORM models |
| `app/db/session.py` | `SessionLocal` factory and `get_db` FastAPI dependency; includes explicit rollback on exception |
| `app/models/operational_record.py` | ORM model for `operational_records` table; Python-side `default=uuid.uuid4` ensures `id` is populated before flush |
| `app/models/analysis_result.py` | ORM model for `analysis_results` table; `summary`, `anomalies`, `prompt`, and `response_raw` are `NOT NULL` (enforced at DB level via Alembic migration) |
| `app/routers/ingestion.py` | CSV upload endpoint; enforces `MAX_UPLOAD_BYTES` limit with HTTP 413 and descriptive message; delegates parsing to `csv_parser.py` |
| `app/routers/webhook.py` | Webhook receiver; Pydantic validation errors are caught by the global handler in `main.py` |
| `app/routers/records.py` | `GET /records` with `limit` and `offset` query parameters (default 100, max 1000) |
| `app/routers/analysis.py` | Triggers `run_analysis`; passes the injected `Session` directly (no secondary sessionmaker) |
| `app/services/csv_parser.py` | Row-level validation; returns `CSVRowError` objects for invalid rows rather than raising |
| `app/services/analysis.py` | Single-pass and map-reduce analysis logic; `_MAX_REDUCE_ITERATIONS = 5` guards the reduce loop; accepts a `Session` directly |
| `app/services/chunking.py` | Splits serialised record lists into token-bounded chunks |
| `app/services/token_counter.py` | Wraps `tiktoken`; encoding is cached with `lru_cache` to avoid repeated model loading |
| `app/services/poller.py` | Async polling loop; validates external timestamps with `datetime.fromisoformat()` before writing to DB |
| `alembic/` | Database migrations; includes migration that enforces `NOT NULL` on `AnalysisResult` text fields |
| `tests/conftest.py` | `DELETE`-based test isolation (single strategy; transaction rollback approach was removed) |
| `docker-compose.yml` | No hardcoded secrets; database credentials are injected via env var substitution from `.env`; source code volume mount removed |
| `.env.example` | Documents all required variables including `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` |

### Deviations from Original Spec

**Minor addition beyond stated scope — pagination on `GET /records`:**
The original spec listed pagination on `GET /records` as explicitly OUT of scope. During review, the absence of a row limit was flagged as a non-blocking concern (returning unbounded result sets is a correctness risk in production). Pagination was added as `limit` (default 100, max 1000) and `offset` query parameters. This is a backwards-compatible, additive change that does not break any existing caller and satisfies the spirit of the unified retrieval requirement. The spec's OUT section is retained as written to reflect the original design intent.

### Post-Review Fixes Summary

The following issues were identified during code review and resolved before the feature was marked complete:

| Issue | Fix Applied |
|-------|-------------|
| Webhook 422 response body used FastAPI's default `{"detail": [...]}` format instead of the spec's `{"errors": [...]}` shape | Added global `RequestValidationError` handler in `app/main.py` |
| CSV 413 response had an empty body | `ingestion.py` now raises `HTTPException(status_code=413, detail=...)` with a descriptive message |
| `AnalysisResult` fields `summary`, `anomalies`, `prompt`, `response_raw` were `nullable=True` in the DB | Changed to `nullable=False`; covered by an Alembic migration |
| Analysis router created a secondary `sessionmaker` bound to the injected session | Refactored: `run_analysis` now accepts a `Session` directly |
| Hardcoded `apppassword` in `docker-compose.yml` | Replaced with env var substitution; `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` added to `.env.example` |
| Unbounded `while` loop in reduce phase | Replaced with `for _ in range(_MAX_REDUCE_ITERATIONS)` with a convergence guard |
| Poller wrote unvalidated timestamp strings from the external mock server directly to the ORM | Added `datetime.fromisoformat()` parsing in `poller.py` |
| `tiktoken.encoding_for_model` called on every token count invocation | Encoding cached with `lru_cache` in `token_counter.py` |
| `get_db` did not explicitly rollback on exception | Explicit rollback added in `db/session.py` |
| Dual test isolation (transaction rollback + DELETE cleanup) | Simplified to `DELETE`-only cleanup in `conftest.py` |
| `OperationalRecord.id` had no Python-side default | Added `default=uuid.uuid4` so `id` is populated before flush |
