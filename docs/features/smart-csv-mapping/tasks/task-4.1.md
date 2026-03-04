---
id: task-4.1
title: Write new column mapping tests
complexity: high
method: tdd
blocked_by: [task-2.1, task-3.1]
blocks: []
files: [tests/test_csv_ingestion.py]
---

## Description
Write the full suite of new tests covering all 10 success criteria end-to-end via the router. Add an `_upload_with_mapping()` helper alongside the existing `_upload()`. All new test code goes in `test_csv_ingestion.py` — this task owns all additions to this file.

## Actions
1. Add `_upload_with_mapping(client, content, mapping, filename)` helper that passes `data={"column_mapping": json.dumps(mapping)}` alongside `files`.
2. Write tests for each SC:
   - SC1: Canonical columns → 201 + identity `mappings_applied`
   - SC2: Alias columns (`site_id`, `metric`, `value`) → 201 + alias `mappings_applied`
   - SC3: Explicit `column_mapping` + alias composition → 201
   - SC4: Extra columns silently discarded
   - SC5: Unresolvable column → 422
   - SC6: Explicit mapping referencing absent column → 422
   - SC7: Ambiguous columns (both `entity_id` and `site_id`) → 422
   - SC8: Case-insensitive matching (`ENTITY_ID`, `Site_ID`)
   - SC9: Alias table completeness (unit test on `COLUMN_ALIASES` dict)
   - SC10: Row-level error with aliased CSV uses canonical field name in error message
3. All tests use the wrapper response shape: `response.json()["records"]`, `response.json()["mappings_applied"]`.

## Acceptance
- [ ] 10+ test functions, one per SC minimum
- [ ] All tests pass with `pytest tests/test_csv_ingestion.py`
- [ ] Tests use same fixture pattern as existing tests (client, db_session)
- [ ] No test depends on implementation internals beyond public API
