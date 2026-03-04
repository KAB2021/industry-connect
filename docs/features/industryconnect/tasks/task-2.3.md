---
id: task-2.3
title: Background poller with mock server
complexity: high
method: tdd
blocked_by: [task-1.2, task-1.3]
blocks: [task-4.1]
files: [app/services/poller.py, app/main.py, docs/mock-server-schema.md, tests/test_poller.py]
---

## Description
Implement an asyncio background poller in the FastAPI lifespan. Uses httpx.AsyncClient to fetch records from POLL_SOURCE_URL on POLL_INTERVAL_SECONDS interval. Persists as OperationalRecord with source='poll', analysed=False. Document the mock server's expected response schema. Use TDD with respx.

## Actions
1. Write `tests/test_poller.py` — mock external server with respx; trigger poll cycle; verify OperationalRecord created with source='poll' and analysed=False; verify poller handles HTTP errors gracefully; verify configurable interval
2. Implement `app/services/poller.py` — `async def poll_once(session_factory, client)` and `async def run_poller(session_factory, settings)` with `while True: try/except: await asyncio.sleep(interval)`
3. Update `app/main.py` lifespan to create poller task on startup, cancel on shutdown
4. Create `docs/mock-server-schema.md` documenting the expected response schema from POLL_SOURCE_URL (JSON array of records with timestamp, entity_id, metric_name, metric_value)
5. Run tests and ensure all pass

## Edge Cases
- HTTP 5xx from source: log error, continue polling
- HTTP timeout: log, continue
- Malformed JSON response: log, skip cycle
- Shutdown during sleep: task cancellation must be clean

## Acceptance
- [ ] Poller fetches from POLL_SOURCE_URL at POLL_INTERVAL_SECONDS intervals
- [ ] Each fetched record persisted as OperationalRecord with source='poll', analysed=False
- [ ] Poller runs as asyncio task in lifespan, cancels cleanly on shutdown
- [ ] HTTP errors and malformed responses do not crash the poller loop
- [ ] Tests use respx to mock external server
- [ ] Mock server response schema is documented in `docs/mock-server-schema.md`
