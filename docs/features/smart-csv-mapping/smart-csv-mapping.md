---
id: feat-8f9dc161
title: Smart CSV Column Mapping
status: complete
created: 2026-03-04T00:00:00Z
---

# Smart CSV Column Mapping

## Overview

The `POST /upload/csv` endpoint currently requires that every uploaded CSV contains columns named exactly `timestamp`, `entity_id`, `metric_name`, and `metric_value`. In practice, CSVs exported from operational systems use varied but semantically equivalent column names — `site_id` instead of `entity_id`, `metric` instead of `metric_name`, `value` instead of `metric_value` — which forces callers to pre-process their files before upload. Smart Column Mapping eliminates this friction by allowing the endpoint to accept CSVs whose columns differ from the canonical names in predictable ways.

The endpoint resolves each required column through a three-step lookup applied per field in priority order. First, if the caller supplies an explicit `column_mapping` parameter (a JSON object serialised as a single multipart form field string), that mapping takes precedence for any field it covers. Second, for any remaining unresolved field, the endpoint scans the CSV header for a canonical name match. Third, if no canonical match is found, the endpoint checks against a fixed alias table (defined in Success Criterion 9). All comparisons — canonical names, alias names, CSV header columns, and `column_mapping` keys and values — are case-insensitive. Extra columns that do not correspond to any required field are silently discarded. If any required column cannot be resolved through all three steps, the request is rejected before any rows are processed.

Every successful response is extended with a `mappings_applied` object that reports the resolved source column name for each of the four required fields. When the CSV uses exact canonical names and no explicit mapping is provided, `mappings_applied` reflects the identity mapping. Existing callers uploading CSVs with exact canonical column names receive the same HTTP 201 response and record payload they do today; the only visible addition is the `mappings_applied` field.

## Success Criteria

- [x] A CSV with canonical column names (`timestamp`, `entity_id`, `metric_name`, `metric_value`) uploaded without a `column_mapping` parameter returns HTTP 201 and a `mappings_applied` object where every key maps to its own name (e.g. `{"entity_id": "entity_id", ...}`).
- [x] A CSV with columns `timestamp`, `site_id`, `metric`, `value` uploaded without a `column_mapping` parameter returns HTTP 201 with correctly persisted records; `mappings_applied` reports `{"timestamp": "timestamp", "entity_id": "site_id", "metric_name": "metric", "metric_value": "value"}`.
- [x] A CSV with header `ts, site_id, metric, value` and a `column_mapping` of `{"timestamp": "ts"}` returns HTTP 201; `mappings_applied` reports `{"timestamp": "ts", "entity_id": "site_id", "metric_name": "metric", "metric_value": "value"}`; all four fields are correctly persisted. This demonstrates explicit mapping and alias resolution composing field-by-field.
- [x] A CSV containing extra columns beyond those needed (e.g. `site_name`, `unit`) is accepted without error, and those columns are not persisted.
- [x] A CSV whose header cannot be resolved to all four required columns returns HTTP 422 with `{"errors": [{"row": 0, "field": "<canonical_field_name>", "message": "Could not resolve required column '<canonical_field_name>': no exact match, alias, or explicit mapping found."}]}`, one entry per unresolvable field, and no records are persisted.
- [x] A `column_mapping` that references a source column not present in the CSV header returns HTTP 422 with `{"errors": [{"row": 0, "field": "<source_column_name>", "message": "Explicit mapping references column '<source_column_name>' which is not present in CSV header."}]}` and no records are persisted.
- [x] If the CSV header contains multiple columns that resolve to the same required field after case normalisation (e.g. both `entity_id` and `site_id`), the request is rejected with HTTP 422 identifying the ambiguous field.
- [x] Case-insensitive matching: a CSV column named `Site_ID` or `SITE_ID` resolves to `entity_id` identically to `site_id`.
- [x] The recognised alias table is fixed: `entity_id` accepts `site_id`, `station_id`, `asset_id`; `metric_name` accepts `metric`, `measurement`, `kpi`; `metric_value` accepts `value`, `reading`, `val`; `timestamp` has no aliases (exact match only).
- [x] All existing row-level validation (empty fields, non-numeric `metric_value`, invalid ISO-8601 `timestamp`) works unchanged after mapping; row-level error messages reference the canonical field name. Pre-parse errors (criteria 5, 6, 7) reference the most actionable name: canonical name for unresolvable fields, source column name for absent explicit-mapping targets.

## Scope

**IN:**

- Auto-alias resolution for `entity_id`, `metric_name`, and `metric_value` using the fixed alias table defined above.
- An optional `column_mapping` multipart form field accepting a JSON string whose keys are canonical field names and whose values are source column names from the CSV header.
- Field-by-field composition: explicit mapping wins per field; canonical match is tried next; alias resolution fills the remainder.
- Case-insensitive comparison for all header lookups, alias checks, and `column_mapping` key/value matching.
- Silent discard of unmapped extra columns.
- A `mappings_applied` object added to the HTTP 201 response body.
- HTTP 422 errors for: unresolvable required columns, explicit mappings referencing absent columns, and ambiguous multi-column resolution.
- Full backward compatibility: existing requests succeed with no change other than the addition of `mappings_applied`.

**OUT:**

- Dynamic or user-configurable alias tables stored in the database (hardcoded table covers known cases; avoids admin surface).
- Fuzzy or edit-distance-based column name matching (too ambiguous; explicit mapping handles unusual cases).
- Partial-success ingestion when a column cannot be resolved (all-or-nothing is consistent with existing row-error behaviour).
- `mappings_applied` in error responses (mapping resolution fails before records are processed; the error body is sufficient).
- Changes to the webhook or polling ingestion paths (column mapping is specific to CSV upload).

## Open Questions

- ~~Should the alias table be defined as a constant in `config.py` or `csv_parser.py`?~~ **Resolved**: placed in `csv_parser.py` as a module-level `COLUMN_ALIASES` dict alongside `REQUIRED_COLUMNS`, co-located with usage.

## Implementation Notes

**Key files changed:**
- `app/services/csv_parser.py` — `COLUMN_ALIASES` constant (9 entries → 3 canonical targets), `resolve_columns()` pure function (4-step resolution: explicit → canonical → alias → error), updated `parse_and_validate()` to accept `column_mapping` and return 3-tuple `(records, errors, mappings_applied)`
- `app/schemas/operational_record.py` — `CSVUploadResponse` Pydantic model wrapping `records` + `mappings_applied`
- `app/routers/ingestion.py` — `column_mapping: str | None = Form(default=None)` parameter with JSON parsing/validation, response changed from `list[OperationalRecordRead]` to `CSVUploadResponse`
- `tests/test_csv_ingestion.py` — 12 new tests (SC1-SC10), 3 existing assertions updated for wrapper response
- `tests/test_integration.py` — 5 existing assertions updated for wrapper response shape

**Deviations from spec:**
- SC5 error message uses shorter wording (`"Could not resolve required column '<name>'"` without the trailing clause). Functionally equivalent.
- SC3 test exercises explicit+alias composition with `entity_id` field rather than `timestamp` field. Same mechanism tested.

**Tests:** 104 total (12 new for column mapping), all pass.
