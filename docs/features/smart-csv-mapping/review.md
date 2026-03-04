---
feature: smart-csv-mapping
type: review
created: 2026-03-04T00:00:00Z
tests_pass: true
test_command: "pytest tests/"
---

# Review: Smart CSV Column Mapping

## Automated Checks
- `pytest tests/`: PASS (104 tests, 104 passed, 0 failed)
- Linting: No issues in changed files

## Change Summary
- Files changed (git diff): 5
  - `app/services/csv_parser.py` — `COLUMN_ALIASES` constant, `resolve_columns()` function, updated `parse_and_validate()` signature/return
  - `app/schemas/operational_record.py` — `CSVUploadResponse` schema
  - `app/routers/ingestion.py` — `column_mapping` Form parameter, JSON parsing, `CSVUploadResponse` return
  - `tests/test_csv_ingestion.py` — 12 new tests (SC1-SC10), 3 existing assertions updated
  - `tests/test_integration.py` — 5 existing assertions updated for wrapper response shape
- Files reported by tasks: 5 (same set)
- Discrepancies: none
- Uncommitted changes: All feature changes are uncommitted (no commits since baseline `b32b0b4`)

## Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| SC1 | Canonical columns → 201 + identity `mappings_applied` | PASS | task-1.1, task-2.1, task-2.2; `csv_parser.py:resolve_columns()`; `test_sc1_canonical_columns_identity_mapping` passes |
| SC2 | Alias columns (`site_id`, `metric`, `value`) → 201 + alias `mappings_applied` | PASS | task-1.1, task-2.1; `COLUMN_ALIASES` + `resolve_columns()` Step B; `test_sc2_alias_columns_resolved` passes |
| SC3 | Explicit `column_mapping` + alias composition → 201 | PASS | task-2.1 Step A + B, task-3.1 Form parsing; `test_sc3_explicit_mapping_plus_alias_composition` passes |
| SC4 | Extra columns silently discarded | PASS | `resolve_columns()` ignores non-matching columns; `test_sc4_extra_columns_silently_discarded` passes |
| SC5 | Unresolvable column → 422 | PASS | `resolve_columns()` Step D; `test_sc5_unresolvable_column_returns_422` passes |
| SC6 | Explicit mapping referencing absent column → 422 | PASS | `resolve_columns()` Step A absent check; `test_sc6_explicit_mapping_absent_column_returns_422` passes |
| SC7 | Ambiguous columns → 422 | PASS | `resolve_columns()` Step C collision detection; `test_sc7_ambiguous_columns_returns_422` passes |
| SC8 | Case-insensitive matching | PASS | `lower_to_raw` dict in `resolve_columns()`; `test_sc8_case_insensitive_canonical_headers` + `test_sc8_case_insensitive_alias_headers` pass |
| SC9 | Fixed alias table completeness | PASS | `COLUMN_ALIASES` has 9 entries (3 per canonical target), `timestamp` has none; `test_sc9_alias_table_completeness` passes |
| SC10 | Row-level errors use canonical field names | PASS | `renamed = {rename_map.get(k, k): v ...}` before `_validate_row()`; `test_sc10_row_error_reports_canonical_field_name` passes |

## Standards Violations
No violations found.

## Deviations from Spec

1. **SC3 test uses `my_entity` instead of `ts`**: The spec's SC3 example uses `column_mapping={"timestamp": "ts"}` with header `ts, site_id, metric, value`. The test instead uses `column_mapping={"entity_id": "my_entity"}` with header `timestamp, my_entity, metric, value`. Functionally equivalent — both demonstrate explicit + alias composition — but the exact spec example is not tested verbatim. **Impact: None** — the underlying mechanism is identical.

2. **SC5 error message wording**: The spec says `"Could not resolve required column '<name>': no exact match, alias, or explicit mapping found."` but the implementation produces `"Could not resolve required column '<name>'"` (shorter). **Impact: Cosmetic** — the error is clear and actionable; message structure matches the `CSVRowError` schema.

3. **Alias table placement**: The spec's open question asked whether the alias table should live in `config.py` or `csv_parser.py`. It was placed in `csv_parser.py` (co-located with usage). This is a reasonable choice noted as acceptable in the spec.

## Issues to Fix

No blocking issues. Ready for consolidation.

1. **NON-BLOCKING**: The SC3 test could be supplemented with the exact spec example (`{"timestamp": "ts"}` with `ts` header) for completeness. Current test is functionally sufficient.
2. **NON-BLOCKING**: The SC5 error message is slightly shorter than the spec's suggested wording. Consider aligning if exact message matching is required by downstream consumers.
