---
id: task-1.4
title: Create API client layer with typed fetch wrapper
complexity: medium
method: write-test
blocked_by: [task-1.3]
blocks: [task-2.2]
files: [frontend/src/api/client.ts, frontend/src/api/types.ts]
standards: []
---

## Description
Create a typed API client layer using native `fetch`. Define TypeScript interfaces matching the backend schemas (OperationalRecord, AnalysisResult, ErrorResponse, Anomaly). Create wrapper functions for each endpoint that handle status-code-based error parsing: 422 returns `ErrorResponse` shape (`{"errors": [...]}`), 413 returns `{"detail": "..."}` shape. All functions use `VITE_API_BASE_URL` as the base URL.

## Actions
1. Create `frontend/src/api/types.ts` with TypeScript interfaces:
   - `OperationalRecord`: id (string), source (string), timestamp (string), entity_id (string), metric_name (string), metric_value (number), analysed (boolean), ingested_at (string)
   - `AnalysisResult`: id (string), record_ids (string[]), summary (string), anomalies (Anomaly[]), prompt (string), response_raw (string), prompt_tokens (number|null), completion_tokens (number|null), created_at (string)
   - `Anomaly`: record_id (string), metric_name (string), metric_value (number), explanation (string)
   - `CSVRowError`: row (number), field (string), message (string)
   - `ErrorResponse`: errors (CSVRowError[])
   - `ApiError` class extending Error with `status`, `detail?`, `errors?` fields
2. Create `frontend/src/api/client.ts` with functions:
   - `fetchRecords(limit?: number, offset?: number): Promise<OperationalRecord[]>` — GET /records
   - `uploadCSV(file: File): Promise<OperationalRecord[]>` — POST /upload/csv with FormData
   - `triggerAnalysis(): Promise<AnalysisResult[]>` — POST /analyse
   - `healthCheck(): Promise<{status: string}>` — GET /health
3. Each function throws `ApiError` with parsed error body on non-2xx responses

## Edge Cases
- 413 errors return `{"detail": "..."}` — parse into `ApiError.detail`
- 422 errors return `{"errors": [...]}` — parse into `ApiError.errors`
- Network errors (fetch rejects) — wrap in `ApiError` with status 0

## Acceptance
- [ ] All backend endpoint schemas have matching TypeScript interfaces
- [ ] Each API function handles 2xx, 413, and 422 responses correctly
- [ ] `ApiError` class carries status code and parsed error body
- [ ] Base URL is read from `VITE_API_BASE_URL` env var
