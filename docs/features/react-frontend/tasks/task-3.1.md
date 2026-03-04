---
id: task-3.1
title: Build Dashboard view
complexity: medium
method: write-test
blocked_by: [task-2.1, task-2.2]
blocks: [task-4.1]
files: [frontend/src/pages/DashboardPage.tsx]
standards: []
---

## Description
Replace the Dashboard placeholder with a landing page that shows summary stats: total records loaded, count of records pending analysis (`analysed === false`), and the most recent analysis result from the current session. Uses the `useRecords` hook to fetch data.

## Actions
1. Use `useRecords` to fetch the first page of records
2. Compute summary stats from the loaded data:
   - Total records count (from loaded page)
   - Pending analysis count (filter where `analysed === false`)
3. Display a section for the most recent analysis result (passed via React context or local state — initially shows "No analysis run yet")
4. Style with Tailwind: stat cards in a grid layout, clean typography

## Acceptance
- [ ] Dashboard renders at `/` by default
- [ ] Shows total records and pending analysis count from loaded data
- [ ] Shows "No analysis run yet" when no analysis has been triggered this session
- [ ] Styled with Tailwind CSS (stat cards, consistent spacing)
