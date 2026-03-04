---
id: task-3.1
title: Update ingestion router for column_mapping and CSVUploadResponse
complexity: medium
method: refactor
blocked_by: [task-1.2, task-2.2]
blocks: [task-4.1, task-4.2]
files: [app/routers/ingestion.py]
---

## Description
Modify the CSV upload endpoint to accept an optional `column_mapping` JSON string via Form parameter, parse it safely, pass it to `parse_and_validate`, and return `CSVUploadResponse` instead of a bare list.

## Actions
1. Add `column_mapping: str | None = Form(default=None)` parameter to `upload_csv`.
2. Parse `column_mapping` with `json.loads()` wrapped in `try/except json.JSONDecodeError` — return 422 with `CSVRowError(row=0, field="column_mapping", message="...")` on failure. Also validate it's a dict with string keys/values.
3. Unpack 3-tuple from `parse_and_validate(content, parsed_mapping)`.
4. Change `response_model` from `list[OperationalRecordRead]` to `CSVUploadResponse`.
5. Construct return: `CSVUploadResponse(records=[OperationalRecordRead.model_validate(r) for r in orm_records], mappings_applied=mappings_applied)`.
6. Import `json`, `Form`, `CSVUploadResponse`.

## Acceptance
- [ ] Returns `{"records": [...], "mappings_applied": {...}}` for valid uploads
- [ ] Malformed `column_mapping` JSON returns 422, not 500
- [ ] Non-dict `column_mapping` (e.g. JSON array) returns 422
- [ ] Omitting `column_mapping` entirely still works (backward compatible request)
- [ ] OpenAPI schema reflects `CSVUploadResponse`
