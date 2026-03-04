---
feature: react-frontend
type: task-root
total_tasks: 11
total_batches: 5
---

# Tasks: React Frontend

## Goal
Build a React SPA that provides a browser-based interface for all IndustryConnect backend capabilities: viewing records, uploading CSVs, and triggering LLM analysis.

## Success Criteria Map
| Criterion (from feature doc) | Tasks |
|------------------------------|-------|
| React app loads, renders Dashboard at root URL | task-1.3, task-2.1, task-3.1 |
| Records table with columns (source, entity_id, metric_name, metric_value, timestamp, analysed, ingested_at) | task-3.2 |
| Records pagination controls via offset | task-3.2 |
| Records filtering by source | task-3.2 |
| Records auto-polls + manual refresh | task-3.2 |
| Upload valid CSV shows success count | task-3.3 |
| Upload invalid CSV displays 422 errors | task-3.3 |
| Upload 413 file-too-large error | task-3.3 |
| Analysis trigger displays all results | task-3.4 |
| Analysis button disabled when no unanalysed records | task-3.4 |
| Analysis 413 error display | task-3.4 |
| Session-only analysis history (reverse chronological) | task-3.4 |
| Client-side routing (no full page reload) | task-2.1 |
| Tailwind CSS clean/minimal styling | task-1.3, task-3.1, task-3.2, task-3.3, task-3.4 |
| Frontend build produces static assets | task-1.3, task-4.1 |
| CORS middleware on FastAPI backend | task-1.1 |

## Phases
1. **Phase 1: Foundation** — task-1.1, task-1.2, task-1.3, task-1.4
2. **Phase 2: Core Infrastructure** — task-2.1, task-2.2
3. **Phase 3: Views** — task-3.1, task-3.2, task-3.3, task-3.4
4. **Phase 4: Docker Integration** — task-4.1
