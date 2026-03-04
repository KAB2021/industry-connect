---
id: task-2.2
title: Set up TanStack Query provider and API hooks
complexity: medium
method: write-test
blocked_by: [task-1.4]
blocks: [task-3.1, task-3.2, task-3.3, task-3.4]
files: [frontend/src/hooks/useRecords.ts, frontend/src/hooks/useUploadCSV.ts, frontend/src/hooks/useAnalysis.ts, frontend/src/main.tsx]
standards: []
---

## Description
Install TanStack Query and create custom hooks that wrap the API client functions. Set up the `QueryClientProvider` in the app entry point. Each hook encapsulates the data fetching pattern for its view.

## Actions
1. Install `@tanstack/react-query` in `frontend/`
2. Wrap the app in `<QueryClientProvider>` in `frontend/src/main.tsx`
3. Create `frontend/src/hooks/useRecords.ts`:
   - `useRecords(limit, offset)` — `useQuery` calling `fetchRecords`, with `refetchInterval` set from `VITE_POLL_INTERVAL_MS` env var (default 30000ms)
   - Returns `{ data, isLoading, error, refetch }` for manual refresh
4. Create `frontend/src/hooks/useUploadCSV.ts`:
   - `useUploadCSV()` — `useMutation` calling `uploadCSV`
   - Returns `{ mutate, isPending, isSuccess, isError, error, data, reset }`
5. Create `frontend/src/hooks/useAnalysis.ts`:
   - `useAnalysis()` — `useMutation` calling `triggerAnalysis`
   - Returns `{ mutate, isPending, isSuccess, isError, error, data, reset }`

## Acceptance
- [ ] `QueryClientProvider` wraps the app
- [ ] `useRecords` auto-polls at the configured interval
- [ ] `useRecords` supports manual refetch via `refetch()`
- [ ] `useUploadCSV` handles file upload mutations
- [ ] `useAnalysis` handles analysis trigger mutations
