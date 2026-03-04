---
id: task-2.2
title: Webhook ingestion endpoint with validation
complexity: medium
method: tdd
blocked_by: [task-1.2, task-1.3]
blocks: [task-4.1]
files: [app/routers/ingestion.py, tests/test_webhook_ingestion.py]
---

## Description
Implement POST /webhook endpoint. Accept JSON body validated against WebhookPayload schema. Check request Content-Length against 10MB, return 413 if exceeded. If validation fails, return 422 with ErrorResponse where row=0. If valid, create OperationalRecord with source='webhook', analysed=False. Use TDD.

## Actions
1. Write `tests/test_webhook_ingestion.py` — valid webhook creates record with analysed=False; invalid webhook returns 422 with row=0 errors; oversized webhook returns 413; record retrievable after creation
2. Add POST /webhook route to `app/routers/ingestion.py` — validate, persist or return errors
3. Run tests and ensure all pass

## Acceptance
- [ ] Valid webhook returns 201 and persists OperationalRecord with source='webhook' and analysed=False
- [ ] Invalid webhook returns 422 with `{"errors": [{"row": 0, "field": "X", "message": "Y"}]}`
- [ ] Webhook exceeding 10MB returns 413
- [ ] Tests cover: happy path, 422 with row=0, 413
