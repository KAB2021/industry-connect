---
id: task-3.2
title: Build Records view with table, pagination, filtering, sorting, and auto-poll
complexity: high
method: write-test
blocked_by: [task-2.1, task-2.2]
blocks: [task-4.1]
files: [frontend/src/pages/RecordsPage.tsx, frontend/src/components/RecordsTable.tsx]
standards: []
---

## Description
Build the Records view with a table displaying OperationalRecord entries. Implements server-side pagination via `limit`/`offset` query params, client-side filtering by `source`, client-side sorting by `timestamp` or `ingested_at`, auto-polling, and a manual refresh button.

## Actions
1. Create `RecordsPage.tsx` that manages pagination state (`offset`, `limit` defaulting to 100)
2. Use `useRecords(limit, offset)` hook for data fetching with auto-poll
3. Create `RecordsTable.tsx` component:
   - Columns: source, entity_id, metric_name, metric_value, timestamp, analysed (badge), ingested_at
   - Sortable column headers for timestamp and ingested_at (client-side `Array.sort()` over loaded records)
   - Filter dropdown/buttons for source: All, csv, webhook, poll (client-side `Array.filter()`)
4. Add pagination controls:
   - "Previous" / "Next" buttons that adjust `offset` by `limit`
   - Disable "Previous" when offset is 0
   - Disable "Next" when returned records count < limit (no more pages)
5. Add a "Refresh" button that calls `refetch()` from the `useRecords` hook
6. Style with Tailwind: clean table with alternating row colors, filter buttons, pagination controls

## Edge Cases
- Empty record set: show "No records found" message instead of empty table
- Sorting + filtering apply only to the currently loaded page of records
- Auto-poll continues running while user interacts with filters/sort

## Acceptance
- [ ] Table displays all 7 columns for records returned by `GET /records`
- [ ] Pagination controls fetch next/previous pages via offset
- [ ] Source filter shows only matching records from the current page
- [ ] Sorting by timestamp or ingested_at reorders the current page
- [ ] Auto-polls at `VITE_POLL_INTERVAL_MS` interval (default 30s)
- [ ] Manual refresh button triggers immediate data fetch
- [ ] Empty state displays "No records found"
