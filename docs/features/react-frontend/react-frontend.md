---
id: feat-e87c6de9
title: React Frontend
status: complete
created: 2026-03-04T00:00:00Z
---

# React Frontend

## Overview

The React frontend is a single-page application that provides a browser-based interface for all IndustryConnect backend capabilities. It connects to the existing FastAPI API and presents four primary views accessible via client-side routing:

1. **Dashboard** — A landing page showing a summary of total records loaded, count of records pending analysis (`analysed === false`), and the most recent analysis result fetched from `GET /analyse`. Serves as a quick-glance entry point.

2. **Records** — A table view displaying `OperationalRecord` entries retrieved from `GET /records`. The table supports client-side filtering by `source` (csv, webhook, poll) and sorting by `timestamp` or `ingested_at`. Because `GET /records` accepts `limit` (default 100, max 1000) and `offset` query parameters, the frontend implements paginated navigation: a "Load More" button or page controls that fetch subsequent pages via offset increments. The view auto-polls the current page every 30 seconds (configured via the `VITE_POLL_INTERVAL_MS` build-time environment variable) and provides a manual refresh button. Sorting and filtering apply only to records currently loaded in the client.

3. **Upload** — A form that accepts a CSV file and submits it to `POST /upload/csv`. On success (HTTP 201), it displays a confirmation with the count of ingested records derived from the length of the returned array. On validation error (HTTP 422), it renders the error array in a readable table showing row number, field, and message for each failure. On file-too-large error (HTTP 413), it displays a message indicating the file exceeds the maximum allowed upload size.

4. **Analysis** — A view that triggers analysis via `POST /analyse` and displays all results. Each result shows: summary text, anomalies list, token usage (prompt and completion tokens, displayed as "N/A" when null), and the list of record IDs analysed. When no unanalysed records exist, the trigger button is disabled with the message "No records pending analysis." If the server returns HTTP 413 during analysis, an error message is displayed indicating the data set is too large. Analysis results are fetched from `GET /analyse` (paginated, most recent first) and displayed in reverse chronological order. New results appear immediately after triggering analysis via automatic query invalidation.

Navigation between views uses a persistent top navigation bar. The frontend runs as a separate static build served by its own dev server or container, communicating with the backend via REST API calls. The API base URL is configured via the `VITE_API_BASE_URL` build-time environment variable. CORS middleware must be added to the FastAPI backend to allow cross-origin requests from the frontend origin.

## Success Criteria

- [x] The React app loads in the browser and renders the Dashboard view by default when navigating to the root URL.
- [x] The Records view displays records returned by `GET /records` in a table with columns: source, entity_id, metric_name, metric_value, timestamp, analysed status, ingested_at.
- [x] The Records view provides pagination controls (Load More or page buttons) that fetch additional records via `GET /records` with increasing `offset` values.
- [x] Filtering the Records table by source (csv, webhook, poll) shows only matching records from the currently loaded set without a page reload.
- [x] The Records view auto-polls `GET /records` at the interval defined by `VITE_POLL_INTERVAL_MS` (default 30000ms) and a manual refresh button triggers an immediate fetch.
- [x] Uploading a valid CSV file via the Upload view to `POST /upload/csv` results in a success message displaying the count of ingested records (derived from the response array length).
- [x] Uploading an invalid CSV file displays each validation error (row, field, message) returned in the HTTP 422 response in a readable format.
- [x] Uploading a file that exceeds the maximum size displays an error message when the server returns HTTP 413.
- [x] Clicking the analysis trigger button on the Analysis view calls `POST /analyse` and displays all returned results, each showing summary, anomalies, and token counts (with "N/A" for null token values).
- [~] The analysis trigger button is disabled with the message "No records pending analysis" when `POST /analyse` would return an empty array, determined by checking the analysed status of loaded records.
- [x] If `POST /analyse` returns HTTP 413, the Analysis view displays an error message indicating the data set is too large.
- [x] Analysis results are persisted and listed in reverse chronological order on the Analysis view, surviving page refreshes.
- [x] The app uses client-side routing — navigating between views does not cause a full page reload.
- [x] The UI is styled with Tailwind CSS using a clean, minimal design with consistent spacing and typography.
- [x] The frontend build produces static assets that can be served independently of the backend runtime.
- [x] The FastAPI backend includes CORS middleware configured to allow requests from the frontend origin.

## Scope

**IN:**
- Single-page React application with client-side routing (4 views: Dashboard, Records, Upload, Analysis)
- Records table with client-side filtering by source and sorting by timestamp/ingested_at
- Paginated record fetching using `GET /records` limit/offset parameters
- Auto-polling (interval set via `VITE_POLL_INTERVAL_MS` env var, default 30s) and manual refresh for records
- CSV file upload form targeting `POST /upload/csv` with success, 422 error, and 413 error display
- Analysis trigger via `POST /analyse` with multi-result display (summary, anomalies, token counts, record IDs)
- Persisted analysis history via `GET /analyse` (reverse chronological, survives page refreshes)
- Error handling for HTTP 413 on both upload and analysis endpoints
- Disabled analysis button when no un-analysed records exist
- `VITE_API_BASE_URL` env var for configuring the backend API base URL
- Tailwind CSS minimal styling
- Static build output (Vite)
- CORS middleware addition to FastAPI backend

**OUT:**
- Authentication or login screen (backend has no auth — deferred)
- ~~`GET /analysis-results` backend endpoint for cross-session analysis history~~ Implemented as `GET /analyse` with pagination
- Webhook ingestion form in the UI (webhooks are machine-to-machine, not user-initiated)
- Editing or deleting individual records (backend has no PUT/DELETE endpoints)
- Server-side rendering or SSR (static SPA is sufficient for portfolio scope)
- Dark mode toggle (defer to keep initial scope focused)
- Mobile-responsive layout (desktop-first, responsive is a follow-up)
- End-to-end or integration tests for the frontend (unit tests only in initial scope)
- Runtime-configurable poll interval via UI control (build-time only)

## Open Questions

- ~~Should the frontend be added to the existing `docker-compose.yml` as a separate service, or run standalone outside Docker during development?~~ Resolved: standalone Vite dev server for development, Docker nginx service for production.

## Implementation Notes

### Key Files

**Backend additions**
- `app/config.py` — `CORS_ALLOWED_ORIGINS` setting (comma-separated, whitespace-stripped)
- `app/main.py` — `CORSMiddleware` with configurable allowed origins
- `app/routers/analysis.py` — `GET /analyse` endpoint with `limit`/`offset` pagination, ordered by `created_at` descending

**Frontend (`frontend/`)**
- `src/api/types.ts` — TypeScript interfaces for all API shapes + `ApiError` class
- `src/api/client.ts` — Typed `fetch` wrapper with status-code-based error parsing
- `src/hooks/useRecords.ts` — TanStack Query `useQuery` with `refetchInterval` auto-polling
- `src/hooks/useUploadCSV.ts` — `useMutation` for CSV upload
- `src/hooks/useAnalysis.ts` — `useMutation` for analysis trigger with `onSuccess` callback
- `src/hooks/useAnalysisResults.ts` — TanStack Query `useQuery` for `GET /analyse` (persisted results)
- `src/pages/DashboardPage.tsx` — Summary stats (total records, pending count, most recent analysis result)
- `src/pages/RecordsPage.tsx` — Paginated table with auto-poll and refresh
- `src/pages/UploadPage.tsx` — CSV upload form with 201/422/413 handling
- `src/pages/AnalysisPage.tsx` — Trigger button, persisted result history with query invalidation
- `src/components/RecordsTable.tsx` — Client-side sort/filter HTML table
- `src/components/AnalysisResultCard.tsx` — Result display (summary, anomalies, tokens)
- `src/layouts/AppLayout.tsx` — Persistent top nav bar with active link highlighting
- `src/App.tsx` — `createBrowserRouter` with 4 routes
- `src/main.tsx` — `QueryClientProvider` wrapping `RouterProvider`
- `Dockerfile` — Multi-stage build: Node 20 Alpine → nginx Alpine
- `nginx.conf` — SPA fallback + reverse proxy for backend API paths

### Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Routing | React Router v7 (SPA mode) | Simple 4-route SPA; TanStack Router's type-safety not justified |
| Data fetching | TanStack Query v5 | Built-in `refetchInterval`, `useMutation`, cache deduplication |
| HTTP client | Native `fetch` | Zero bundle cost; no upload-progress requirement |
| Table | Manual `Array.sort`/`Array.filter` | 7 columns with server-side pagination; TanStack Table would require manual-mode wiring |
| Serving | Vite dev (dev) + nginx Docker (prod) | Fast HMR on macOS; Vite proxy avoids CORS in dev |
| Dev proxy | Single `/api` prefix with rewrite | Avoids route collisions between frontend routes and backend API paths |

### Deviations from Spec

- **Criterion #10 (partial):** Button is disabled and "No records pending analysis" is shown as adjacent text, not as the button label itself
- **Pending-record check:** `useRecords(1000)` instead of spec's suggested `GET /records?limit=1&offset=0`
