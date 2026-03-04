---
id: task-1.2
title: SQLAlchemy models and Alembic migration
complexity: medium
method: write-test
blocked_by: [task-1.1]
blocks: [task-1.3, task-2.1, task-2.2, task-2.3, task-3.1, task-3.2]
files: [app/models/operational_record.py, app/models/analysis_result.py, app/models/__init__.py, alembic/versions/001_initial_models.py]
---

## Description
Define the two core SQLAlchemy ORM models and generate the initial Alembic migration. The migration file must be committed — Docker entrypoint and CI both run `alembic upgrade head`.

## Actions
1. Create `app/models/operational_record.py` — OperationalRecord: id (UUID PK, server_default uuid4), source (String, enum: csv|webhook|poll), timestamp (DateTime UTC), entity_id (String), metric_name (String), metric_value (Float), analysed (Boolean, default False), ingested_at (DateTime, server_default utcnow)
2. Create `app/models/analysis_result.py` — AnalysisResult: id (UUID PK), record_ids (JSON, list of UUID strings), summary (Text), anomalies (JSON), prompt (Text), response_raw (Text), prompt_tokens (Integer), completion_tokens (Integer), created_at (DateTime, server_default utcnow)
3. Update `app/models/__init__.py` to import both models and expose Base
4. Generate Alembic migration: `alembic revision --autogenerate -m "initial_models"`
5. Verify migration applies cleanly: `alembic upgrade head` and `alembic downgrade base`

## Acceptance
- [ ] `alembic upgrade head` creates both tables in PostgreSQL
- [ ] `alembic downgrade base` drops both tables
- [ ] OperationalRecord.analysed defaults to False when inserted
- [ ] Both models importable from `app.models`
- [ ] Migration file is committed in `alembic/versions/`
