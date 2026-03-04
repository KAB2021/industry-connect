---
feature: industryconnect
type: research
created: 2026-03-04T00:00:00Z
---

# Research: IndustryConnect

## Relevant Code

No existing codebase — this is a greenfield project. The project structure from the overview document defines the target layout:

```
app/main.py, app/config.py, app/models/, app/schemas/, app/routers/, app/services/, app/db/
```

## Patterns & Standards

No existing coding standards documents. The following conventions should be established for this project based on research:

- **Sync database, async where it matters**: Database layer uses sync SQLAlchemy with psycopg2. Route handlers are defined as `def` (not `async def`), and FastAPI automatically runs them in a thread pool. Async is used for the poller (asyncio lifespan loop) and LLM calls (OpenAI SDK uses httpx internally). This avoids async SQLAlchemy gotchas while still demonstrating async skills.
- **Alembic works out of the box**: With sync SQLAlchemy, Alembic needs no special async configuration. Standard `env.py` setup.
- **Poller must use async I/O**: The lifespan-based poller runs in the event loop — any blocking call inside it (e.g. `time.sleep`, sync HTTP) will freeze the app. Use `httpx.AsyncClient` for the poller's HTTP calls.

## External Findings

### Background Task Scheduling (Poller)

| Option | Periodic | Extra Deps | Async-native | Multi-worker Safe |
|---|---|---|---|---|
| FastAPI `BackgroundTasks` | No (one-off only) | None | Yes | N/A |
| `asyncio` loop in lifespan | Yes | None | Yes | No |
| APScheduler `AsyncIOScheduler` | Yes | `apscheduler` | Yes | No |
| `fastapi-utils` `@repeat_every` | Yes | `fastapi-utils` | Yes | No |
| Celery Beat | Yes | Celery + broker | No | Yes |

**Finding**: For a single-worker portfolio app, the `asyncio` loop in FastAPI's lifespan event is the simplest approach with zero extra dependencies. APScheduler is a valid alternative if retry/jitter logic is needed later — both have the same multi-worker caveat. The poller loop body must be wrapped in `try/except` to prevent a failed cycle from crashing the loop; failures should be logged.

Sources: [FastAPI Background Tasks docs](https://fastapi.tiangolo.com/tutorial/background-tasks/), [APScheduler with FastAPI](https://rajansahu713.medium.com/implementing-background-job-scheduling-in-fastapi-with-apscheduler-6f5fdabf3186), [Sentry: Schedule tasks with FastAPI](https://sentry.io/answers/schedule-tasks-with-fastapi/)

### SQLAlchemy Sync with psycopg2

Sync SQLAlchemy with psycopg2 is the simpler approach. FastAPI automatically runs `def` route handlers in a thread pool, so sync database calls don't block the event loop. This avoids async SQLAlchemy gotchas: no `MissingGreenlet` errors from lazy loading, no dual-engine Alembic config, and standard tutorials/patterns apply directly. The project demonstrates async skills via the poller and LLM integration — the database layer doesn't need to add complexity for portfolio signal.

Sources: [FastAPI sync vs async performance](https://thedkpatel.medium.com/fastapi-performance-showdown-sync-vs-async-which-is-better-77188d5b1e3a), [psycopg2 vs asyncpg discussion](https://github.com/fastapi/fastapi/discussions/13732), [asyncpg vs psycopg2 benchmarks](https://github.com/AliYmn/fastapi-asyncpg-vs-psycopg2)

### CSV Parsing

Python's stdlib `csv` module with `io.StringIO` is the right choice — no heavy dependencies, row-by-row processing, easy per-row validation with structured error reporting. Pandas is overkill for this use case.

**Encoding risk**: `UploadFile.read()` decoded as UTF-8 will raise `UnicodeDecodeError` on non-UTF-8 files (latin-1, cp1252, BOM). The endpoint must either attempt UTF-8 first with a clean 422 fallback, or explicitly document UTF-8-only and catch the decode error gracefully.

**Validation contract**: Check that required columns exist after reading header. Reject rows with wrong column counts. Handle empty files and header-only files explicitly.

### LLM Integration (OpenAI SDK)

The OpenAI Python SDK returns `response.usage.prompt_tokens` and `response.usage.completion_tokens` directly from chat completion responses — no manual counting needed for logging. For pre-counting tokens before API calls (to decide whether to chunk), use `tiktoken.encoding_for_model("gpt-4.1-mini")` which resolves the correct encoding automatically rather than hardcoding an encoding name.

**Model choice**: GPT-4.1 mini ($0.40/M input, $1.60/M output) vs GPT-4o-mini ($0.15/M input, $0.60/M output). GPT-4.1 mini has a 1M token context window vs 128k for GPT-4o-mini. For map-reduce summarisation where large chunks reduce the number of API calls, the larger context window may offset the higher per-token cost. Decision deferred to decisions.md.

**Retry handling**: The OpenAI SDK has built-in retry logic via `max_retries` on the client constructor. No custom retry wrapper needed.

Sources: [OpenAI token counting cookbook](https://developers.openai.com/cookbook/examples/how_to_count_tokens_with_tiktoken/), [OpenAI API pricing](https://openai.com/api/pricing/), [GPT-4.1 mini model docs](https://platform.openai.com/docs/models/gpt-4.1-mini), [tiktoken tutorial](https://www.datacamp.com/tutorial/tiktoken-library-python)

### Map-Reduce Summarisation

LangChain provides built-in map-reduce chains but adds a heavy transitive dependency tree. For a portfolio project, a custom implementation is straightforward and demonstrates understanding of the pattern rather than framework usage.

**Chunking strategy**: Chunk by token count (targeting ~80% of the model's context window), not by row count. Use tiktoken to measure chunk sizes. Include 2-3 rows of overlap between chunks so context around chunk boundaries is preserved — this prevents splitting related anomalous rows across chunks.

**Reduce step**: If combined chunk summaries exceed context, apply the reduce step recursively until the result fits. In practice, for 10 MB of input, 3-5 chunks with 1-paragraph summaries each will easily fit in one reduce call.

Sources: [LangChain summarisation docs](https://python.langchain.com/docs/use_cases/summarization/), [Map-reduce with LangChain + OpenAI](https://medium.com/@atef.ataya/map-reduce-building-summarization-apps-with-langchain-and-openai-57c05788c7eb), [Token limit strategies](https://www.bretcameron.com/blog/three-strategies-to-overcome-open-ai-token-limits)

### Anomaly Detection Prompting

Research from ICLR 2025 (AnoLLM) and EMNLP 2025 (TABARD) confirms LLMs can detect anomalies in tabular data when data is serialised as JSON in the prompt. Key patterns:

- **Data format**: Convert `OperationalRecord` rows to JSON objects in the prompt
- **Structured outputs**: Use OpenAI's `response_format={"type": "json_schema", ...}` (not just JSON mode) to enforce the exact output schema — this guarantees parseable results
- **Output schema**: `{"anomalies": [{"record_id": str, "metric_name": str, "metric_value": float, "explanation": str}]}` plus a `summary` field
- **System prompt**: Define what constitutes an anomaly for operational data (statistical outliers, impossible values, sudden spikes/drops relative to other records)

Sources: [AnoLLM paper (ICLR 2025)](https://www.amazon.science/publications/anollm-large-language-models-for-tabular-anomaly-detection), [TABARD benchmark](https://aclanthology.org/2025.findings-emnlp.1189.pdf), [LLM anomaly detection guide](https://towardsdatascience.com/boosting-your-anomaly-detection-with-llms/)

### Testing Strategy

| Concern | Tool | Rationale |
|---|---|---|
| Async test runner | `pytest-asyncio` | Standard for async FastAPI testing |
| HTTP test client | `httpx.AsyncClient` | Async-native, works with FastAPI's `TestClient` alternative |
| Test database | Environment variable pointing to local/CI Postgres | Simpler than testcontainers; CI uses a service container, local dev uses a local Postgres instance |
| Mock external HTTP (poller) | `respx` | Async-native httpx mocking, well-maintained |
| Mock OpenAI API | `respx` | The OpenAI SDK uses httpx under the hood; respx can mock it directly without extra plugins |
| CSV upload testing | `httpx.AsyncClient` with multipart form data | Standard pattern |

**Note on testcontainers**: While testcontainers-python can spin up a real Postgres per test session, it requires Docker to be running locally. For a portfolio project where a reviewer might `git clone && pytest`, this is unnecessary friction. A simpler approach: use an environment variable for the test database URL, defaulting to `localhost:5432/industryconnect_test`. CI configures this via a PostgreSQL service container.

Sources: [FastAPI testing docs](https://fastapi.tiangolo.com/tutorial/testing/), [respx docs](https://lundberg.github.io/respx/), [openai-responses plugin](https://pypi.org/project/openai-responses/), [Mocking OpenAI with respx](https://tonyaldon.com/2026-02-12-mocking-the-openai-api-with-respx-in-python/), [testcontainers for Python](https://testcontainers.com/guides/getting-started-with-testcontainers-for-python/)

### Docker Compose

- **Entrypoint pattern**: Shell script that runs `alembic upgrade head` then `exec uvicorn app.main:app`. The healthcheck must verify the application database specifically (`pg_isready -U appuser -d industryconnect`) — default `pg_isready` returns healthy before `init` scripts create the app database. Add a retry loop in the entrypoint as a safety net.
- **depends_on**: Use `condition: service_healthy` to ensure Postgres is ready before the app starts.
- **.env**: `.env.example` committed with all variable names and placeholder values.

Sources: [FastAPI + PostgreSQL + Alembic + Docker setup](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/), [Solving FastAPI + Alembic + Docker](https://hackernoon.com/solving-the-fastapi-alembic-docker-problem), [TestDriven.io FastAPI + SQLModel](https://testdriven.io/blog/fastapi-sqlmodel/)

### GitHub Actions CI

- PostgreSQL service container with healthcheck (`pg_isready`)
- Cache pip dependencies with `actions/cache` keyed on `requirements.txt` hash
- Steps: checkout, setup-python, restore cache, install deps, run alembic, run `ruff check .`, run `mypy`, run pytest
- Linting (`ruff`) and type checking (`mypy`) in CI signals code quality discipline

Sources: [PostgreSQL service container](https://til.simonwillison.net/github-actions/postgresq-service-container), [FastAPI CI with GitHub Actions](https://pyimagesearch.com/2024/11/04/enhancing-github-actions-ci-for-fastapi-build-test-and-publish/), [Full-stack FastAPI template](https://github.com/fastapi/full-stack-fastapi-template)

## Risks

1. **Event loop blocking in poller**: The asyncio poller runs in the event loop — any sync call inside it (sync HTTP, `time.sleep`) stalls the entire app. Likelihood: medium. Impact: frozen request handling. Mitigation: use `httpx.AsyncClient` for poller HTTP calls; wrap the loop body in `try/except`.

3. **CSV encoding failures**: Non-UTF-8 files cause 500 errors instead of 422. Likelihood: medium (real-world CSVs frequently use other encodings). Impact: poor user experience. Mitigation: catch `UnicodeDecodeError` and return 422 with a descriptive message.

4. **Docker startup race condition**: Alembic runs before app database is created. Likelihood: medium on first `docker-compose up`. Impact: app container exits immediately. Mitigation: healthcheck targets the specific app database; entrypoint retries Alembic.

5. **Token count mismatch**: Wrong tiktoken encoding gives inaccurate pre-counts, causing unexpected API errors or oversized requests. Likelihood: low if using `encoding_for_model()`. Impact: failed analysis calls. Mitigation: use model-name-based encoding lookup, not hardcoded encoding.
