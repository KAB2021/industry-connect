---
id: task-2.1
title: Implement resolve_columns() function
complexity: high
method: tdd
blocked_by: [task-1.1]
blocks: [task-2.2, task-4.1]
files: [app/services/csv_parser.py]
---

## Description
The core mapping function. Takes raw CSV fieldnames and an optional explicit mapping dict, resolves each required column through the three-step lookup (explicit → canonical → alias), and returns the rename map plus the `mappings_applied` audit dict. This is a pure function — it must NOT raise HTTPException or import any HTTP concerns. Errors are returned as `CSVRowError` lists, consistent with the existing parser pattern.

## Actions
1. Define signature:
   ```python
   def resolve_columns(
       raw_fields: list[str],
       column_mapping: dict[str, str] | None = None,
   ) -> tuple[dict[str, str], dict[str, str], list[CSVRowError]]:
       # Returns (rename_map, mappings_applied, errors)
   ```
2. Normalise raw fieldnames to lowercase for matching.
3. Step A — apply explicit `column_mapping` entries first. If a mapped source column is not in the header, add a `CSVRowError(row=0, field=source_col, message="Explicit mapping references column '...' which is not present in CSV header.")`.
4. Step B — for each unresolved required column, try canonical match (case-insensitive), then alias match via `COLUMN_ALIASES`.
5. Step C — detect collisions: if two source columns resolve to the same canonical name, add `CSVRowError(row=0, field=canonical, message="Ambiguous: multiple columns resolve to '...'")`.
6. Step D — detect unresolvable: if a required column has no match, add `CSVRowError(row=0, field=canonical, message="Could not resolve required column '...'")`.
7. Build `mappings_applied`: always 4 keys `{canonical: source_col}`, including identity entries.
8. Extra columns not in `rename_map` are silently ignored.

## Edge Cases
- Both `entity_id` and `site_id` in header → collision error (SC7)
- `column_mapping={"entity_id": "ghost"}` where `ghost` not in header → absent ref error (SC6)
- Header with `ENTITY_ID` (uppercase) → case-insensitive canonical match (SC8)
- Header with `Site_ID` (mixed case) → case-insensitive alias match (SC8)
- All case comparisons use `.lower()` consistently

## Acceptance
- [ ] Returns correct rename_map + identity mappings_applied for canonical headers
- [ ] Returns correct alias mappings_applied for aliased headers (SC2)
- [ ] Composes explicit mapping with alias resolution per-field (SC3)
- [ ] Silently ignores extra columns (SC4)
- [ ] Returns CSVRowError for unresolvable columns (SC5)
- [ ] Returns CSVRowError for absent explicit mapping targets (SC6)
- [ ] Returns CSVRowError for ambiguous/collision columns (SC7)
- [ ] All matching is case-insensitive (SC8)
- [ ] Never imports or raises HTTPException
