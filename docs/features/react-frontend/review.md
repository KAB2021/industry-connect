---
feature: react-frontend
type: review
created: 2026-03-04T23:00:00Z
tests_pass: true
test_command: "cd frontend && npx tsc --noEmit && npm run build"
---

# Review: React Frontend

## Automated Checks
- `npx tsc --noEmit`: PASS — zero TypeScript errors
- `npm run build`: PASS — 96 modules, 338 kB JS, 20.6 kB CSS, built in ~500ms
- `npx eslint src/`: FAIL — 3 errors (see Issues #1, #2 below)
- Backend `pytest`: 91 passed, 2 failed — failures are **pre-existing** (CSV/webhook 413 handling bugs from prior feature, not introduced by react-frontend)

## Change Summary
- Files changed/created by feature: 24 implementation files + 11 task state files + docs
- Files reported by tasks: all match actual files on disk
- Discrepancies: task-1.3 state lists stale dist asset filenames (expected — content hashes change on rebuild)
- Uncommitted changes: all feature work is uncommitted (working tree + untracked)
- Unrelated uncommitted files: `CHANGELOG.md`, `README.md`, `sample.csv`, `alembic/versions/8898d1648dd1_...py`, `docs/research/architecture.md` — from prior features, not part of react-frontend

## Success Criteria

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | App loads and renders Dashboard at root URL | PASS | `App.tsx:13` — index route renders `DashboardPage` |
| 2 | Records table with 7 columns | PASS | `RecordsTable.tsx:89-117` — all columns present |
| 3 | Pagination via offset | PASS | `RecordsPage.tsx:8-15` — offset incremented by limit |
| 4 | Client-side source filtering | PASS | `RecordsTable.tsx:29-31` — client-side `Array.filter()` |
| 5 | Auto-poll + manual refresh | PASS | `useRecords.ts:11` — `refetchInterval`, `RecordsPage.tsx:37` — refresh button |
| 6 | Valid CSV upload shows ingested count | PASS | `UploadPage.tsx:88-98` — `data.length` displayed |
| 7 | Invalid CSV shows 422 error table | PASS | `UploadPage.tsx:103-125` — Row/Field/Message table |
| 8 | Oversized file shows 413 error | PASS | `UploadPage.tsx:127-135` — "File exceeds maximum upload size" |
| 9 | Analysis trigger displays results with summary, anomalies, tokens | PASS | `AnalysisResultCard.tsx:78-107` — all fields rendered, "N/A" for null tokens |
| 10 | Analysis button disabled when no pending records | PARTIAL | Button is disabled (`AnalysisPage.tsx:25`), "No records pending analysis" text shown adjacent to button (`line 49`), but button label stays "Run Analysis" rather than changing text |
| 11 | Analysis 413 shows data-too-large error | PASS | `AnalysisPage.tsx:94-109` — "Data set is too large to analyse" |
| 12 | Persisted results in reverse chronological order | PASS | `GET /analyse` ordered by `created_at desc`; `useAnalysisResults` hook + query invalidation after trigger |
| 13 | Client-side routing (no full page reload) | PASS | `App.tsx` — `createBrowserRouter` + `RouterProvider`, `nginx.conf` — `try_files` SPA fallback |
| 14 | Tailwind CSS styling | PASS | All components use Tailwind utility classes, `@tailwindcss/vite` configured |
| 15 | Static build output | PASS | `Dockerfile` — multi-stage Node→nginx, `dist/` produced |
| 16 | CORS middleware on backend | PASS | `main.py:33-38` — `CORSMiddleware` with configurable origins |

**Result: 15 PASS / 1 PARTIAL / 0 FAIL**

## Standards Violations

### CRITICAL

1. **`RecordsTable.tsx:49-58`** — `SortIndicator` component defined inside `RecordsTable` body. Recreated on every render, causing unnecessary remounts. Also flagged by ESLint `react-hooks/static-components`. **Fix:** hoist to module scope and pass `sortKey`/`sortDir` as props.

2. **`nginx.conf`** — No `client_max_body_size` directive. nginx defaults to 1 MB, which will reject CSV uploads >1 MB with a 413 before the request reaches FastAPI's 10 MB guard. **Fix:** add `client_max_body_size 11M;` to the server block.

### WARNING

3. **`AnalysisPage.tsx:18`** — `setState` inside `useEffect` flagged by ESLint `react-hooks/set-state-in-effect`. Causes cascading renders. **Fix:** use `onSuccess` callback in `useMutation` options instead.

4. **`UploadPage.tsx:29`** — Unsafe `error as ApiError` cast. Should use `error instanceof ApiError` (already done correctly in `AnalysisPage.tsx:28` for a different check). **Fix:** `const apiError = isError && error instanceof ApiError ? error : null`.

5. **`AnalysisPage.tsx:104`** — Same unsafe `error as ApiError` cast pattern.

6. **`AnalysisPage.tsx:28`** — Redundant `(error as ApiError).status` cast after `instanceof` check. TypeScript already narrows the type.

7. **`app/main.py:35`** — `CORS_ALLOWED_ORIGINS.split(",")` without whitespace stripping. Origins with spaces (e.g. `"origin1, origin2"`) won't match. **Fix:** `[o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",")]`.

8. **`DashboardPage.tsx:22`** — `useRecords(100)` caps stats at 100 records. Dashboard numbers silently under-count for larger datasets.

9. ~~**`DashboardPage.tsx:70-74`** — "Most Recent Analysis Result" section is a static placeholder never wired to real data.~~ **FIXED:** Now fetches from `GET /analyse` via `useAnalysisResults` and renders the latest result with `AnalysisResultCard`.

10. **`main.tsx:7`** — `QueryClient` created with all defaults. No explicit `retry` or `staleTime` config — will retry 422/413 errors 3 times unnecessarily.

11. **`frontend/.env`** — Not in `.gitignore`. Risk of committing environment config. Should add `.env` to `frontend/.gitignore` or rename to `.env.local`.

## Deviations from Spec

- Criterion #10: spec says button should be disabled "with the message" — implementation shows the message as adjacent text rather than as the button label. Functionally equivalent, presentation difference only.
- `AnalysisPage` fetches `useRecords(1000)` to check pending status, rather than the spec's suggested `GET /records?limit=1&offset=0`. More thorough but slightly heavier.

## Issues to Fix

**BLOCKING (must fix):**
1. **nginx `client_max_body_size`** — CSV uploads >1 MB will fail in Docker. Add `client_max_body_size 11M;` to `frontend/nginx.conf`.
2. **`SortIndicator` inside component** — ESLint error + React performance issue. Hoist to module scope.
3. **`setState` in `useEffect`** — ESLint error. Move to `onSuccess` in mutation options.

**NON-BLOCKING (recommended):**
4. Unsafe `as ApiError` casts → use `instanceof` (UploadPage:29, AnalysisPage:104)
5. CORS split without `.strip()` (main.py:35)
6. Add `.env` to `frontend/.gitignore`
7. Add `restart: unless-stopped` to frontend service in docker-compose.yml

## Post-Completion Fixes (2026-03-04)

The following changes were made after the initial review cycle:

**Vite proxy route collision fix:**
- `vite.config.ts` — Consolidated individual proxy rules (`/records`, `/upload`, `/webhook`, `/analyse`, `/health`) into a single `/api` prefix rule with path rewrite. This prevents Vite from proxying browser navigation requests (e.g. `/records`) to the backend API instead of serving the React SPA.
- `frontend/.env` — `VITE_API_BASE_URL` set to `/api` (was empty)
- `src/api/client.ts` — `BASE_URL` fallback changed from `??` to `||` to correctly handle empty string env values

**Persisted analysis results (replaces session-only history):**
- `app/routers/analysis.py` — Added `GET /analyse` endpoint with `limit`/`offset` pagination, ordered by `created_at desc`
- `src/api/client.ts` — Added `fetchAnalysisResults()` function
- `src/hooks/useAnalysisResults.ts` — New `useQuery` hook for analysis results
- `src/pages/AnalysisPage.tsx` — Replaced session-state history with server-persisted results; invalidates query cache after analysis trigger
- `src/pages/DashboardPage.tsx` — "Most Recent Analysis Result" now renders the latest result from `GET /analyse` (was static placeholder)
- `src/hooks/useAnalysis.ts` — `onSuccess` callback type corrected from `(data: AnalysisResult[]) => void` to `() => void`

**Error handling:**
- `AnalysisPage.tsx` and `DashboardPage.tsx` now surface errors from `useAnalysisResults()` instead of silently showing empty state
