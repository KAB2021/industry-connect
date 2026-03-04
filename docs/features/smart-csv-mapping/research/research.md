---
feature: smart-csv-mapping
type: research
created: 2026-03-04T00:00:00Z
---

# Research: Smart CSV Column Mapping

## Relevant Code

- `app/services/csv_parser.py:9` — `REQUIRED_COLUMNS` set; the alias table should be defined alongside this as a module-level constant (same pattern).
- `app/services/csv_parser.py:42-58` — Header validation: `DictReader` construction, fieldnames guard, and exact-match missing-column check. The mapping logic inserts between line 45 (fieldnames confirmed) and line 50 (missing-column check).
- `app/services/csv_parser.py:63-77` — Row processing references columns by canonical string keys (`row["timestamp"]`, etc.). No changes needed if fieldnames are normalised before this point.
- `app/services/csv_parser.py:93-178` — `_validate_row` references `REQUIRED_COLUMNS` and canonical keys. No changes needed post-mapping.
- `app/services/csv_parser.py:12-14` — `parse_and_validate` signature returns `tuple[list[dict], list[CSVRowError]]`. Must expand to accept `column_mapping` param and return `mappings_applied` as a third tuple element.
- `app/routers/ingestion.py:17-59` — Upload endpoint. Must add `column_mapping: str | None = Form(default=None)`, parse JSON manually, pass to parser, and change response model.
- `app/schemas/operational_record.py:7-18` — `OperationalRecordRead` is shared with webhook and GET /records endpoints. Must NOT modify; use a new wrapper model instead.
- `app/schemas/errors.py:1-11` — `CSVRowError` and `ErrorResponse` models. Reused for mapping-related 422 errors (row=0).
- `tests/test_csv_ingestion.py:31-36` — `_upload()` helper. Need a sibling `_upload_with_mapping()` that passes `data={"column_mapping": json.dumps(mapping)}`.
- `tests/test_integration.py:170,179,198,322` — These lines assert CSV upload response is a raw list (`isinstance(body, list)`, `for record in response.json()`, `len(csv_response.json()) == 3`). All break when response changes to wrapper object. Must be updated.

## Patterns & Standards

- Module-level constants pattern: `REQUIRED_COLUMNS` at `csv_parser.py:9` establishes the precedent for the alias table — a frozen dict in the same file.
- Pure sync service functions: the CSV parser has no I/O; mapping logic should stay pure.
- Error shape: all CSV-related 422s use `{"errors": [CSVRowError(row, field, message)]}`. Mapping errors follow the same shape with `row=0`.
- pydantic-settings in `config.py` exclusively holds environment-injectable runtime values. The alias table is a compile-time constant and does not belong there.
- Test pattern: `TestClient` with `files={}` kwarg for uploads; `httpx` supports `data={}` alongside `files={}` for mixed multipart.

## Risks

- **Breaking response shape**: Changing from `list[OperationalRecordRead]` to `CSVUploadResponse` (wrapper with `records` + `mappings_applied`) breaks every existing caller that expects a raw JSON array. This affects `test_integration.py` (4+ assertions) and any frontend/external consumer of `POST /upload/csv`. Mitigation: since this is a portfolio project with a known internal frontend, accept the breakage and update all call sites. Document the change in the response. If external consumers existed, a versioned endpoint (`/v2/upload/csv`) or a feature flag would be needed instead.
- **Duplicate alias collision**: `csv.DictReader` silently drops duplicate header keys (uses last value). If two source columns map to the same canonical name after alias resolution, data is silently lost with no error. Mitigation: the mapping step must validate uniqueness before mutating fieldnames and return 422 on collision.
- **Malformed `column_mapping` JSON**: `json.loads()` on the Form string will raise `JSONDecodeError`, surfacing as an unhandled 500. The existing `RequestValidationError` handler in `main.py` does not catch `JSONDecodeError`. Mitigation: wrap in `try/except json.JSONDecodeError` and return 422 with `CSVRowError(row=0, field="column_mapping", message="...")`.
- **DictReader fieldnames mutation**: `csv.DictReader.fieldnames` returns a mutable list cached in `self._fieldnames`. Mutating it in-place (e.g., `reader.fieldnames[:] = new_names`) before iteration is safe — Python's csv module reads `self._fieldnames` on each `__next__` call. Verified in CPython source. No risk here.

## Answers to Open Questions

- **Q: Should the alias table be in `config.py` or `csv_parser.py`?** — In `csv_parser.py` as a module-level constant. Evidence: `REQUIRED_COLUMNS` is already a module-level set at line 9 of the same file, establishing the pattern for parser-specific domain constants. `config.py` exclusively holds environment-injectable runtime values (DATABASE_URL, OPENAI_API_KEY, etc.) — the alias table is a compile-time constant that doesn't vary between environments. A separate `column_aliases.py` module would add indirection with no benefit for a ~10-entry dict consumed by one function.
