---
id: task-3.1
title: GET /records endpoint
complexity: low
method: tdd
blocked_by: [task-1.2, task-1.3]
blocks: [task-4.1]
files: [app/routers/records.py, app/main.py, tests/test_records.py]
---

## Description
Implement GET /records returning all OperationalRecord rows regardless of source. Return as list of OperationalRecordRead. Register router in app/main.py. Use TDD.

## Actions
1. Write `tests/test_records.py` — seed records with source='csv', 'webhook', 'poll'; verify GET /records returns all; verify response matches OperationalRecordRead schema; verify empty DB returns empty list
2. Implement `app/routers/records.py` with GET /records route
3. Register records router in `app/main.py`
4. Run tests

## Acceptance
- [ ] GET /records returns all OperationalRecord rows regardless of source
- [ ] Response is list of objects conforming to OperationalRecordRead schema
- [ ] Empty DB returns empty list, not error
