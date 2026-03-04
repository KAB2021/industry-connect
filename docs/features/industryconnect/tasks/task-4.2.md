---
id: task-4.2
title: GitHub Actions CI pipeline
complexity: low
method: write-test
blocked_by: [task-1.1]
blocks: []
files: [.github/workflows/ci.yml]
---

## Description
Create GitHub Actions CI workflow YAML. This is scaffolded early (parallel with models) but only verified green after all tests exist. Uses PostgreSQL service container. Runs alembic, ruff, mypy, then pytest.

## Actions
1. Create `.github/workflows/ci.yml` with Python 3.12 setup
2. Add PostgreSQL 16 service container with healthcheck (`pg_isready -U postgres -d industryconnect_test`)
3. Set TEST_DATABASE_URL environment variable pointing to service container
4. Add steps: checkout, setup-python, pip cache with `actions/cache`, pip install, alembic upgrade head, `ruff check .`, `mypy app/`, `pytest --tb=short -q`
5. Trigger on push to main and pull_request to main

## Acceptance
- [ ] CI workflow file is valid YAML
- [ ] PostgreSQL service container configured with healthcheck
- [ ] TEST_DATABASE_URL set to service container connection string
- [ ] Pipeline includes: alembic migration, ruff lint, mypy type check, pytest
- [ ] Pip dependencies are cached via `actions/cache`
