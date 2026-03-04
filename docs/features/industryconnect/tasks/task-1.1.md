---
id: task-1.1
title: Project scaffolding, configuration, and Docker setup
complexity: medium
method: write-test
blocked_by: []
blocks: [task-1.2, task-1.3, task-2.1, task-2.2, task-2.3, task-3.1, task-3.2, task-4.1, task-4.2, task-5.1]
files: [app/__init__.py, app/main.py, app/config.py, app/db/__init__.py, app/db/session.py, app/models/__init__.py, app/schemas/__init__.py, app/routers/__init__.py, app/services/__init__.py, requirements.txt, .env.example, Dockerfile, docker-compose.yml, alembic.ini, alembic/env.py, tests/__init__.py, tests/conftest.py, pyproject.toml]
---

## Description
Bootstrap the entire project. Create FastAPI app, pydantic-settings config, sync SQLAlchemy session, Docker files, Alembic config, test fixtures, and linting/type-checking config.

## Actions
1. Create all `__init__.py` files for app, app/db, app/models, app/schemas, app/routers, app/services, tests
2. Implement `app/config.py` with `Settings(BaseSettings)`: DATABASE_URL, TEST_DATABASE_URL, OPENAI_API_KEY, OPENAI_MODEL (default `gpt-4o-mini`), POLL_INTERVAL_SECONDS, POLL_SOURCE_URL, MAX_UPLOAD_BYTES (10485760), TOKEN_THRESHOLD
3. Implement `app/db/session.py` with `create_engine(settings.DATABASE_URL)`, `SessionLocal = sessionmaker()`, `get_db` dependency generator
4. Implement `app/main.py` with FastAPI instance, lifespan context manager (empty async body for now), router stubs
5. Create `requirements.txt` with: fastapi, uvicorn[standard], sqlalchemy, psycopg2-binary, alembic, pydantic-settings, python-multipart, httpx, openai, tiktoken, ruff, mypy, pytest, pytest-asyncio, respx, httpx
6. Create `Dockerfile` with Python 3.12 slim, entrypoint script running `alembic upgrade head` then `exec uvicorn`
7. Create `docker-compose.yml` with postgres:16 service (healthcheck: `pg_isready -U appuser -d industryconnect`), app service with `depends_on: condition: service_healthy`
8. Create `.env.example` documenting every variable with placeholder values
9. Configure `alembic.ini` and `alembic/env.py` wired to `settings.DATABASE_URL` and `Base.metadata`
10. Create `tests/conftest.py` with engine/session fixtures using TEST_DATABASE_URL, `create_all`/`drop_all`, TestClient with dependency override
11. Create `pyproject.toml` with ruff and mypy configuration

## Acceptance
- [ ] `from app.config import settings` works and returns populated Settings object
- [ ] FastAPI app starts without errors (empty routes)
- [ ] `docker-compose config` validates without errors
- [ ] Alembic can generate an empty migration
- [ ] `pytest` with an empty test file succeeds and conftest fixtures are importable
- [ ] `ruff check .` and `mypy app/` run without configuration errors
