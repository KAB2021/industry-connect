---
id: task-1.2
title: Add CSVUploadResponse wrapper schema
complexity: low
method: write-test
blocked_by: []
blocks: [task-3.1]
files: [app/schemas/operational_record.py]
---

Create a new Pydantic model `CSVUploadResponse` that wraps the upload response. This replaces the bare `list[OperationalRecordRead]` response with a structured object containing both records and the mapping audit trail.

## Actions
1. Add `CSVUploadResponse` to `app/schemas/operational_record.py`:
   - `records: list[OperationalRecordRead]`
   - `mappings_applied: dict[str, str]` — canonical name (key) → source column name (value), always 4 keys
2. Do NOT modify `OperationalRecordRead` (shared with webhook/records endpoints).

## Acceptance
- [ ] `CSVUploadResponse` instantiates with `records=[]` and a 4-key `mappings_applied` dict
- [ ] JSON round-trip serialises correctly
- [ ] Importable from `app.schemas.operational_record`
