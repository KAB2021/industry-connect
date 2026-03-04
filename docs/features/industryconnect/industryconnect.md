---
id: feat-73dd2524
title: IndustryConnect
status: approved
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

- [ ] A CSV file posted to the upload endpoint is parsed and each valid row persisted as an `OperationalRecord` with `analysed: false` in PostgreSQL.
- [ ] Records ingested via any path are retrievable via `GET /records` in the same request cycle without manual intervention.
- [ ] The background poller fetches from the mock HTTP server on a configurable interval (set via environment variable at startup). After one polling cycle completes — verified by waiting for the configured interval plus a 5-second buffer — at least one `OperationalRecord` with `source: poll` is retrievable via `GET /records`. The mock server's response schema is documented in the project.
- [ ] All persisted records conform to the `OperationalRecord` schema defined in the Overview, regardless of ingestion path.
- [ ] The analysis endpoint processes only records where `analysed` is `false`. After a successful analysis call, those records are marked `analysed: true` and are not re-processed by subsequent analysis calls.
- [ ] Each analysis call persists an `AnalysisResult` row containing: the full rendered prompt string (verbatim), the raw LLM response text, prompt token count, completion token count, a summary string, an anomalies array, and references to the `OperationalRecord` IDs that were included.
- [ ] When the input to the analysis endpoint exceeds the configurable token threshold, the endpoint splits records into chunks, summarises each chunk individually, and produces a final combined summary from the chunk summaries (map-reduce strategy).
- [ ] Inputs exceeding the configurable maximum file size (default 10 MB) are rejected with HTTP 413 and a descriptive error message before any LLM call is made.
- [ ] Posting a CSV with one or more invalid rows returns HTTP 422 with a response body of the shape `{"errors": [{"row": int, "field": str, "message": str}]}`, one entry per invalid row.
- [ ] Posting a malformed or schema-invalid webhook payload returns HTTP 422 with a response body of the same shape: `{"errors": [{"row": int, "field": str, "message": str}]}`, where `row` is 0 for single-object payloads.
- [ ] Given a valid `.env` file present at the project root, `docker-compose up` brings the full stack to a ready state with no additional manual steps.
- [ ] The test suite covers: CSV ingestion (valid and at least one invalid/error path), webhook ingestion (valid and at least one invalid/error path), poll ingestion (at least one cycle producing a persisted record), analysis result persistence (asserting all `AnalysisResult` fields are present and non-null), the `analysed` flag toggle lifecycle, and `GET /records` retrieval.

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
