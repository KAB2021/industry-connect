---
feature: smart-csv-mapping
type: task-root
total_tasks: 7
total_batches: 5
---

# Tasks: Smart CSV Column Mapping

## Goal
Allow the `POST /upload/csv` endpoint to accept CSVs with non-standard column names by auto-resolving known aliases and accepting explicit column mappings, while returning a `mappings_applied` audit object in every successful response.

## Success Criteria Map
| Criterion | Tasks |
|-----------|-------|
| SC1: Canonical columns → 201 + identity mappings | task-2.1, task-2.2, task-3.1, task-4.1 |
| SC2: Alias columns → 201 + alias mappings | task-1.1, task-2.1, task-4.1 |
| SC3: Explicit mapping + alias composition | task-2.1, task-3.1, task-4.1 |
| SC4: Extra columns silently discarded | task-2.1, task-4.1 |
| SC5: Unresolvable columns → 422 | task-2.1, task-4.1 |
| SC6: Absent explicit mapping ref → 422 | task-2.1, task-3.1, task-4.1 |
| SC7: Ambiguous columns → 422 | task-2.1, task-4.1 |
| SC8: Case-insensitive matching | task-2.1, task-4.1 |
| SC9: Fixed alias table | task-1.1, task-4.1 |
| SC10: Row validation unchanged, canonical error names | task-4.1, task-4.2 |

## Phases
1. Phase 1: Foundation — task-1.1, task-1.2
2. Phase 2: Core Logic — task-2.1, task-2.2
3. Phase 3: Router Integration — task-3.1
4. Phase 4: Test Coverage — task-4.1, task-4.2
