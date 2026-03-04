---
id: task-4.2
title: Update existing tests for wrapper response shape
complexity: medium
method: refactor
blocked_by: [task-2.2, task-3.1]
blocks: []
files: [tests/test_integration.py, tests/test_csv_ingestion.py]
---

## Description
The response shape change from `list[OperationalRecordRead]` to `CSVUploadResponse` breaks existing tests. Update all assertions that assume a bare JSON array to unpack from the `records` key. Also verify all pre-existing row-level validation tests still pass unchanged (SC10 regression gate).

## Actions
1. In `tests/test_integration.py`, update the known breaking assertions:
   - Line 170: `assert isinstance(body, list)` → `assert isinstance(body["records"], list)`
   - Line 179: `for record in response.json()` → `for record in response.json()["records"]`
   - Line 198: `for record in response.json()` → `for record in response.json()["records"]`
   - Line 322: `len(csv_response.json()) == 3` → `len(csv_response.json()["records"]) == 3`
   - Scan for any other CSV upload response assertions and update similarly.
2. In `tests/test_csv_ingestion.py`, update existing tests that assert on response shape (the existing 8-9 tests). Change `response.json()` list access to `response.json()["records"]` where applicable.
3. Verify existing row-level validation tests (empty CSV, bad encoding, missing fields, bad timestamps, bad metric_value) still pass — this is the SC10 regression gate.

## Acceptance
- [ ] All previously-passing tests pass again
- [ ] `test_integration.py` lines 170, 179, 198, 322 updated
- [ ] No test silently passes by asserting on a different property
- [ ] `pytest tests/` exits with zero failures
