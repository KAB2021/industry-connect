---
id: task-5.1
title: Docker-compose full-stack validation
complexity: medium
method: write-test
blocked_by: [task-4.1]
blocks: []
files: [docker-compose.yml, Dockerfile, .env.example]
---

## Description
Validate that `docker-compose up` with a valid .env file brings the full stack to ready. Finalise Dockerfile and docker-compose.yml. Verify poller runs in the live stack (SC3 end-to-end). Verify .env.example documents all variables.

## Actions
1. Review and finalise Dockerfile: entrypoint script with retry loop for alembic, then uvicorn
2. Review docker-compose.yml: postgres healthcheck targets app database specifically, app depends_on with condition service_healthy, env_file, port mapping
3. Verify .env.example has every required variable with descriptions
4. Verify all routers registered in app/main.py
5. Validate poller runs in the live stack: after startup, wait POLL_INTERVAL_SECONDS + 5s buffer, then GET /records should show source='poll' records (SC3 live validation)
6. Run full test suite one final time

## Acceptance
- [ ] `docker-compose up` builds and starts both services without errors
- [ ] App waits for postgres to be healthy before starting
- [ ] Alembic migration runs automatically on app startup (with retry on race condition)
- [ ] GET /records returns 200 after stack is ready
- [ ] Poller creates records with source='poll' after one interval (SC3 live test)
- [ ] .env.example documents all environment variables
- [ ] Full test suite passes
