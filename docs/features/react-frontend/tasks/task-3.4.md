---
id: task-3.4
title: Build Analysis view with trigger, results display, and session history
complexity: high
method: write-test
blocked_by: [task-2.1, task-2.2]
blocks: [task-4.1]
files: [frontend/src/pages/AnalysisPage.tsx, frontend/src/components/AnalysisResultCard.tsx]
standards: []
---

## Description
Build the Analysis view with a trigger button, results display, and session-only history. The trigger calls `POST /analyse` and displays all returned results. Each result shows summary, anomalies, token counts, and record IDs. Session history accumulates results from all trigger calls during the current browser session, displayed in reverse chronological order.

## Actions
1. Create `AnalysisPage.tsx` with:
   - A "Run Analysis" trigger button using `useAnalysis().mutate()`
   - Session history stored in component state (`useState<AnalysisResult[][]>([])`) — each trigger call appends its results array
   - Button disabled state: use `useRecords` to check if any records have `analysed === false`. If none, disable button with message "No records pending analysis"
2. Create `AnalysisResultCard.tsx` component displaying:
   - Summary text
   - Anomalies list (each showing record_id, metric_name, metric_value, explanation)
   - Token usage: prompt_tokens and completion_tokens (display "N/A" when null)
   - Record IDs list (collapsible or scrollable if long)
   - Hide `prompt` and `response_raw` fields by default (these are large)
3. On 413 error: display "Data set is too large to analyse" message
4. On success: prepend new results to session history, display all results in reverse chronological order
5. Show loading state with "Analysing..." while mutation is in progress
6. Style with Tailwind: result cards, anomaly list, token usage badges

## Edge Cases
- `POST /analyse` returns empty array (no unanalysed records): button should already be disabled, but also handle gracefully if race condition occurs
- Multiple results from a single trigger (map-reduce): display all, with the final reduce result first or clearly labeled
- Token counts are null: display "N/A"
- Anomalies array is empty: display "No anomalies detected"

## Acceptance
- [ ] Trigger button calls `POST /analyse` and displays all returned results
- [ ] Each result shows summary, anomalies, and token counts ("N/A" for null)
- [ ] Button disabled with "No records pending analysis" when no unanalysed records exist
- [ ] 413 error displays appropriate error message
- [ ] Session history lists all results in reverse chronological order
- [ ] Empty anomalies array shows "No anomalies detected"
- [ ] `prompt` and `response_raw` fields are hidden by default
