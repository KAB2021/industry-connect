---
id: task-2.1
title: CSV upload endpoint with parsing, validation, and persistence
complexity: high
method: tdd
blocked_by: [task-1.2, task-1.3]
blocks: [task-4.1]
files: [app/routers/ingestion.py, app/services/csv_parser.py, app/main.py, tests/test_csv_ingestion.py]
---

## Description
Implement POST /upload/csv endpoint. Accept multipart file upload. Check file size against MAX_UPLOAD_BYTES (10MB), return 413 if exceeded. Parse CSV using csv.DictReader via io.StringIO. Validate each row: collect errors per-row with {row, field, message}. If any validation errors, return 422 with ErrorResponse. If valid, create OperationalRecord per row with source='csv', analysed=False. Use TDD.

## Actions
1. Write `tests/test_csv_ingestion.py` — test cases: valid CSV creates records with analysed=False; CSV over 10MB returns 413; CSV with invalid rows returns 422 with correct error shape; empty CSV returns 422; non-UTF-8 CSV returns 422 with descriptive message; records appear in DB after upload
2. Implement `app/services/csv_parser.py` — `parse_and_validate(file_content: bytes) -> tuple[list[dict], list[CSVRowError]]`; catch UnicodeDecodeError and return 422 with encoding error message; check required columns exist; reject rows with wrong column counts
3. Implement `app/routers/ingestion.py` — POST /upload/csv route: read file, check size, call parser, persist or return errors
4. Register ingestion router in `app/main.py`
5. Run tests and ensure all pass

## Edge Cases
- Non-UTF-8 encoded CSV: catch UnicodeDecodeError, return 422 with descriptive encoding error message (not 500)
- Empty file or header-only file: return 422
- Rows with mismatched column counts: include in per-row errors

## Acceptance
- [ ] Valid CSV upload returns 201 and persists OperationalRecord rows with analysed=False and source='csv'
- [ ] CSV exceeding 10MB returns HTTP 413 with descriptive message
- [ ] CSV with invalid rows returns HTTP 422 with `{"errors": [{"row": N, "field": "X", "message": "Y"}]}`
- [ ] Non-UTF-8 CSV returns HTTP 422 (not 500) with encoding error message
- [ ] Empty CSV or header-only CSV returns HTTP 422
- [ ] All persisted records conform to OperationalRecord schema
- [ ] Tests cover: happy path, 413, 422 row-level, encoding error, empty file
