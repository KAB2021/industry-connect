---
feature: industryconnect
type: review
created: 2026-03-04T00:00:00Z
tests_pass: true
test_command: ".venv/bin/python -m pytest tests/ -v"
---

# Review: IndustryConnect

## Automated Checks
- `ruff check .`: PASS (0 errors)
- `mypy app/`: PASS (0 issues in 24 source files)
- `pytest tests/ -v`: PASS (93 tests, 93 passed, 0 failed, 1.24s)

## Change Summary
- Files changed: 82
- Files reported by tasks: 82
- Discrepancies: none — every file claimed in task state files exists on disk
- Uncommitted changes: none — working tree clean

## Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | CSV upload → OperationalRecord with analysed=false | **PASS** | `ingestion.py:25-60`, `csv_parser.py:75-77`, tested in `test_csv_ingestion.py` and `test_integration.py` |
| 2 | All ingestion paths → retrievable via GET /records | **PASS** | `records.py:11-13` queries all rows, tested in `test_integration.py:313-342` (all 3 sources) |
| 3 | Background poller on configurable interval, source='poll' | **PASS** | `poller.py:54-75` uses `POLL_INTERVAL_SECONDS` env var, tested in `test_poller.py` and `test_integration.py:266-284` |
| 4 | All records conform to OperationalRecord schema | **PASS** | Single ORM model used by all 3 paths, tested in `test_integration.py:346-377` |
| 5 | Analysis processes only analysed=false, marks true, no reprocessing | **PASS** | `analysis.py:166-169` filters, `analysis.py:136-140` marks, tested in `test_analysis_endpoint.py:104-204` and `test_integration.py:433-575` |
| 6 | AnalysisResult persists all required fields | **PARTIAL** | All fields populated in happy path. Gap: all non-key fields are `nullable=True` in DB schema; a malformed LLM response could produce null values without error |
| 7 | Map-reduce when tokens exceed threshold | **PASS** | `analysis.py:181-269` splits, maps, reduces. Tested in `test_analysis_service.py:422-503` |
| 8 | >10 MB → HTTP 413 with descriptive error | **PARTIAL** | Size check is correctly placed before LLM call on all paths. Gap: CSV upload returns `Response(status_code=413)` with empty body — no descriptive message. Webhook and analysis paths return descriptive errors |
| 9 | CSV invalid rows → 422 with `{"errors": [...]}` | **PASS** | `csv_parser.py` produces `CSVRowError` objects, `ingestion.py:40-46` returns `ErrorResponse`. Tested in `test_csv_ingestion.py:96-107` |
| 10 | Malformed webhook → 422 with `{"errors": [{"row": 0, ...}]}` | **FAIL** | Webhook uses FastAPI's default `WebhookPayload` validation which returns `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` — not the specified `{"errors": [...]}` format. No custom exception handler exists. Tests only assert status code, not body shape |
| 11 | docker-compose up → full stack ready, no manual steps | **PASS** | Healthcheck, depends_on condition, alembic retry loop in entrypoint, all env vars configured |
| 12 | Test suite covers all specified scenarios | **PARTIAL** | All areas covered except: webhook invalid body shape not asserted (only status code); analysis result null-field edge case not tested |

## Standards Violations

### Critical
- `analysis.py:66` — Double-session architecture: router creates a second sessionmaker bound to the injected session's connection. Fragile transaction boundaries; should pass `db` directly or make `run_analysis` fully self-contained
- `analysis.py:18` — Return type `-> list` is unparameterised; should be `-> list[AnalysisResult]`
- `poller.py:36` — Unvalidated timestamp string from external source written directly to ORM without parsing or timezone normalisation
- `docker-compose.yml:8` — Hardcoded database password (`apppassword`) in version-controlled file; should use env var substitution
- `analysis.py:274` — Bare `except Exception` rollback can mask original error if rollback itself fails
- `ingestion.py:29-46` — Raw `Response` returns bypass FastAPI's exception handling; inconsistent with webhook/analysis patterns that use `HTTPException`
- `conftest.py:27-34` — Dual test isolation strategy (transaction rollback + DELETE cleanup) can produce inconsistent isolation when services bypass the test session

### Warnings
- `db/session.py:20-26` — `get_db` doesn't explicitly rollback on exception; relies on implicit close behaviour
- `operational_record.py:13-17` — Server-side UUID default only; no Python-side `default=uuid.uuid4` means `id` is `None` until flush
- `analysis.py:228-233` — Unbounded `while` loop in reduce phase; no max-iteration guard
- `poller.py:19` — Synchronous DB writes inside `async def` blocks the event loop
- `records.py:12` — No pagination on GET /records; returns all rows
- `token_counter.py:8` — `tiktoken.encoding_for_model` called on every invocation; should cache with `lru_cache`
- `docker-compose.yml:36` — Source code volume mount (`.:/app`) should not be used in production
- `schemas/analysis_result.py:14,22` — `list[Any]` and `Any` disable Pydantic validation for `record_ids` and `anomalies`

## Deviations from Spec
- **Criterion 10**: Webhook 422 error response uses FastAPI's default validation format instead of the specified `{"errors": [{"row": 0, "field": str, "message": str}]}` shape
- **Criterion 8**: CSV 413 response has no descriptive error message body (empty response)

## Issues to Fix

### BLOCKING
1. **Webhook 422 body format (Criterion 10)**: Register a `RequestValidationError` exception handler in `app/main.py` that converts FastAPI validation errors to `{"errors": [{"row": 0, "field": str, "message": str}]}` format for the webhook endpoint. Update webhook tests to assert body shape, not just status code

### NON-BLOCKING
2. **CSV 413 descriptive error (Criterion 8)**: Change `ingestion.py:35` from `return Response(status_code=413)` to include a descriptive JSON body matching the webhook/analysis patterns
3. **AnalysisResult nullable fields (Criterion 6)**: Consider adding NOT NULL constraints for `prompt`, `response_raw`, `summary` at the DB level
4. **Double-session in analysis router**: Refactor to pass `db` session directly or make `run_analysis` fully self-contained
5. **Poller timestamp validation**: Parse and validate timestamps before writing to DB
6. **Hardcoded DB password**: Move to env var substitution in docker-compose.yml
7. **Reduce loop guard**: Add max-iteration limit to prevent infinite loop
8. **Test isolation**: Choose one strategy (rollback OR delete cleanup), not both
9. **Webhook test body assertions**: Extend tests to verify the 422 response body shape
