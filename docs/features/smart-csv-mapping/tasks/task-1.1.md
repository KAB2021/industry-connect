---
id: task-1.1
title: Define alias table constant in csv_parser.py
complexity: low
method: write-test
blocked_by: []
blocks: [task-2.1]
files: [app/services/csv_parser.py]
---

Add a module-level `COLUMN_ALIASES` dict to `csv_parser.py` alongside the existing `REQUIRED_COLUMNS` constant. Maps each known alias (lowercase) to its canonical column name.

## Actions
1. Below `REQUIRED_COLUMNS` at line 9, add:
   - `site_id` → `entity_id`, `station_id` → `entity_id`, `asset_id` → `entity_id`
   - `metric` → `metric_name`, `measurement` → `metric_name`, `kpi` → `metric_name`
   - `value` → `metric_value`, `reading` → `metric_value`, `val` → `metric_value`
   - `timestamp` has no aliases (exact match only per SC9)
2. Type as `dict[str, str]`. All keys lowercase.

## Acceptance
- [ ] `COLUMN_ALIASES` importable from `app.services.csv_parser`
- [ ] Contains exactly 9 entries mapping to 3 canonical targets
- [ ] No key in `COLUMN_ALIASES` duplicates a key in `REQUIRED_COLUMNS`
