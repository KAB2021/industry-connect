---
feature: industryconnect
type: task-root
total_tasks: 12
total_batches: 7
---

# Tasks: IndustryConnect

## Goal
Build a FastAPI backend that ingests operational data via CSV upload, webhook, and background polling, normalises it into PostgreSQL, and uses an LLM to generate plain-English summaries and anomaly flags with map-reduce chunking for large inputs.

## Success Criteria Map
| Criterion | Tasks |
|-----------|-------|
| SC1: CSV upload persists OperationalRecord | task-2.1, task-4.1 |
| SC2: GET /records returns all sources | task-3.1, task-4.1 |
| SC3: Poller fetches on interval, records appear | task-2.3, task-4.1, task-5.1 |
| SC4: All records conform to schema | task-1.2, task-1.3, task-2.1, task-2.2, task-2.3, task-3.1, task-4.1 |
| SC5: Analysis processes only unanalysed, marks true | task-3.2, task-3.3, task-4.1 |
| SC6: AnalysisResult persisted with all fields | task-3.2, task-3.3, task-4.1 |
| SC7: Map-reduce chunking for large inputs | task-3.2 |
| SC8: 10MB rejection with HTTP 413 | task-2.1, task-2.2, task-3.3 |
| SC9: CSV invalid rows → 422 with error shape | task-1.3, task-2.1 |
| SC10: Invalid webhook → 422 with row=0 | task-1.3, task-2.2 |
| SC11: docker-compose up works | task-1.1, task-4.2, task-5.1 |
| SC12: Test suite covers all paths | task-4.1, task-5.1 |

## Phases
1. **Foundation** — task-1.1, task-1.2, task-1.3
2. **Ingestion Paths** — task-2.1, task-2.2, task-2.3
3. **Retrieval & Analysis** — task-3.1, task-3.2, task-3.3
4. **Integration & CI** — task-4.1, task-4.2
5. **Docker Validation** — task-5.1
