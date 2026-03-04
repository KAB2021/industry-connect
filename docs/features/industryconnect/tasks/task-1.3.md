---
id: task-1.3
title: Pydantic schemas for API request/response validation
complexity: medium
method: write-test
blocked_by: [task-1.1, task-1.2]
blocks: [task-2.1, task-2.2, task-2.3, task-3.1, task-3.3]
files: [app/schemas/operational_record.py, app/schemas/analysis_result.py, app/schemas/errors.py, app/schemas/__init__.py]
---

## Description
Create Pydantic v2 schemas for all API contracts. These enforce SC4 conformity at the API boundary and define the SC9/SC10 error shape.

## Actions
1. Create `app/schemas/operational_record.py` — OperationalRecordRead (model_config: from_attributes=True), WebhookPayload with required fields (timestamp, entity_id, metric_name, metric_value)
2. Create `app/schemas/analysis_result.py` — AnalysisResultRead, AnalysisResponse
3. Create `app/schemas/errors.py` — CSVRowError(row: int, field: str, message: str), ErrorResponse(errors: list[CSVRowError])
4. Update `app/schemas/__init__.py` to re-export all schemas
5. Add schema unit tests verifying validation rules and error shape

## Acceptance
- [ ] OperationalRecordRead can serialize an OperationalRecord ORM instance
- [ ] ErrorResponse produces JSON matching `{"errors": [{"row": int, "field": str, "message": str}]}`
- [ ] WebhookPayload rejects payloads missing required fields
- [ ] All schemas importable from `app.schemas`
