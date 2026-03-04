---
feature: industryconnect
type: decisions
created: 2026-03-04T00:00:00Z
---

# Technical Decisions: IndustryConnect

## Decision 1: Background Poller Scheduling

### Options
| Option | Pros | Cons |
|---|---|---|
| `asyncio` loop in lifespan | Zero dependencies, simple, async-native | No built-in retry/jitter, manual error handling |
| APScheduler `AsyncIOScheduler` | Retry logic, cron-like scheduling, mature library | Extra dependency, same multi-worker caveat |

### Recommendation
**asyncio loop in lifespan** — simplest option with no extra dependencies. The poller is a straightforward interval-based fetch; cron scheduling and retry logic are not needed. Wrap the loop body in `try/except` to log failures without crashing. Both options have the same multi-worker limitation, so APScheduler offers no advantage there for a single-worker app.

---

## Decision 2: SQLAlchemy Sync with psycopg2

### Options
| Option | Pros | Cons |
|---|---|---|
| Sync (psycopg2) | Simple setup, Alembic works out of the box, no MissingGreenlet errors, FastAPI runs `def` routes in thread pool automatically | Sync database layer in an async framework |
| Async (asyncpg) | Native async, consistent async stack | Lazy loading disabled (MissingGreenlet), Alembic needs dual-engine setup, steeper learning curve, hours of debugging for minimal portfolio payoff |

### Recommendation
**Sync with psycopg2** — the project already demonstrates async skills via the poller (asyncio lifespan), LLM calls (httpx-based OpenAI SDK), and mock HTTP testing (respx). The database layer doesn't need async at portfolio scale. Sync SQLAlchemy avoids the MissingGreenlet gotcha, works with Alembic out of the box, and lets route handlers use simple `def` functions that FastAPI automatically runs in a thread pool. Time saved on async debugging is better spent on features that are visible to a reviewer.

---

## Decision 3: LLM Model for Summarisation

### Options
| Option | Input Cost | Output Cost | Context Window | Notes |
|---|---|---|---|---|
| GPT-4.1 mini | $0.40/M tokens | $1.60/M tokens | 1M tokens | Larger context reduces chunking needs |
| GPT-4o-mini | $0.15/M tokens | $0.60/M tokens | 128K tokens | 2.7x cheaper per token |

### Recommendation
**GPT-4o-mini as default, configurable via environment variable** — for a portfolio project where the developer pays out of pocket, the 2.7x cost savings matter. The 128K context window is more than sufficient for most map-reduce chunks. The model name should be a `.env` variable so it can be swapped to GPT-4.1 mini (or any other model) without code changes.

---

## Decision 4: Map-Reduce Implementation

### Options
| Option | Pros | Cons |
|---|---|---|
| LangChain chains | Built-in map-reduce, well-tested | Heavy dependency tree, abstracts away the logic |
| Custom implementation | Zero extra deps, demonstrates understanding, full control | Must handle chunking and recursion manually |

### Recommendation
**Custom implementation** — the map-reduce pattern is ~50 lines of code (chunk by token count with tiktoken, summarise each chunk, combine summaries). Using LangChain for this one feature pulls in a large dependency for minimal benefit. A custom implementation demonstrates understanding of the pattern, which is more impressive for a portfolio piece than importing a chain.

---

## Decision 5: Test Database Strategy

### Options
| Option | Pros | Cons |
|---|---|---|
| testcontainers-python | Real Postgres per test session, fully isolated | Requires Docker running locally, slow startup |
| Environment variable + local Postgres | Simple, no Docker required for tests, CI uses service container | Developer must have Postgres installed or running |

### Recommendation
**Environment variable approach** — use `DATABASE_TEST_URL` defaulting to `postgresql://localhost:5432/industryconnect_test`. CI configures this via a PostgreSQL service container. Local dev uses a local Postgres instance. This avoids the Docker dependency for `pytest` and reduces friction for anyone reviewing the portfolio project.

---

## Decision 6: Mocking OpenAI in Tests

### Options
| Option | Pros | Cons |
|---|---|---|
| `respx` (raw) | Mocks httpx directly, zero extra deps beyond test suite, well-maintained | Must construct OpenAI response JSON manually |
| `openai-responses` plugin | Higher-level API, no manual JSON construction | In maintenance mode, maintainer may deprecate and archive it |

### Recommendation
**respx** — the OpenAI SDK uses httpx under the hood, so respx can intercept all API calls. Constructing the mock response JSON is a one-time fixture. The `openai-responses` plugin is [in maintenance mode](https://github.com/mharrisb1/openai-responses-python) with the maintainer stating it may be deprecated if maintenance exceeds 2 hours/month — not a safe dependency.
