---
id: task-2.2
title: Update parse_and_validate signature and integrate resolve_columns
complexity: medium
method: refactor
blocked_by: [task-2.1]
blocks: [task-3.1, task-4.2]
files: [app/services/csv_parser.py]
---

## Description
Modify `parse_and_validate` to accept a `column_mapping` parameter, call `resolve_columns` at the insertion point (after fieldnames guard, before the old missing-column check), apply the rename map to DictReader rows, and return a 3-tuple including `mappings_applied`.

## Actions
1. Update signature to:
   ```python
   def parse_and_validate(
       file_content: bytes,
       column_mapping: dict[str, str] | None = None,
   ) -> tuple[list[dict], list[CSVRowError], dict[str, str]]:
   ```
2. After the `fieldnames is None` guard (line 45), call `resolve_columns(list(reader.fieldnames), column_mapping)`.
3. If `resolve_columns` returns errors, return them immediately (no row processing).
4. Remove the old `missing_cols` check (lines 50-58) — `resolve_columns` now owns this.
5. Mutate `reader.fieldnames` in-place to use canonical names, OR rename row dicts before passing to `_validate_row`.
6. Ensure `_validate_row` receives rows keyed by canonical names so error messages are canonical (SC10).
7. Return `(records, errors, mappings_applied)` — third element from `resolve_columns`.

## Acceptance
- [ ] Calling with `column_mapping=None` and canonical headers behaves identically to pre-change
- [ ] Calling with aliased headers resolves correctly
- [ ] Row-level error messages reference canonical field names, not source names
- [ ] 3-tuple return is correctly unpacked by callers
- [ ] Extra columns do not appear in row dicts and cause no errors
