---
id: task-3.2
title: Reskin RecordsPage and RecordsTable
complexity: high
method: refactor
blocked_by: [task-2.1]
blocks: []
files: [frontend/src/pages/RecordsPage.tsx, frontend/src/components/RecordsTable.tsx]
standards: []
---

## Description
Apply the Midnight Neon theme to the Records page and its shared `RecordsTable` component. This covers filter chips, table styling, status badges, row striping, and pagination controls.

## Actions
1. **RecordsPage.tsx:** Replace secondary button styling (`border border-gray-300 bg-white`) with glass-style (`bg-surface border border-border text-text-secondary hover:border-border-hover`). Update pagination text from `text-gray-500` to `text-text-muted`.
2. **RecordsTable.tsx — Filter chips:** Replace active chip `bg-blue-600 text-white` with cyan glow style: `bg-sidebar-active text-primary-light border border-primary/20 shadow-glow`. Inactive chips: `bg-surface border border-border text-text-secondary hover:border-border-hover`.
3. **RecordsTable.tsx — Table:** Replace header `bg-gray-50` with `bg-surface`. Update row striping ternary (`idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'`) to `idx % 2 === 0 ? 'bg-transparent' : 'bg-white/[2%]'`. Table borders use `border-border`.
4. **RecordsTable.tsx — Status badges:** Replace `bg-green-100 text-green-800` with `bg-success-bg text-success`. Replace `bg-yellow-100 text-yellow-800` with `bg-warning-bg text-warning`.
5. Update all remaining `text-gray-*` classes to the appropriate text hierarchy token.

## Edge Cases
- Row striping ternary at the specific line must be updated in-place — do not refactor the ternary structure, just swap the class values
- Entity IDs using `font-mono bg-gray-100` should become `font-mono bg-white/5 text-text-secondary`

## Acceptance
- [ ] Filter chips show cyan glow when active, glass style when inactive
- [ ] Table header and rows use dark theme colours
- [ ] Row striping alternates between transparent and subtle white overlay
- [ ] Status badges use semantic colours (green analysed, amber pending)
- [ ] Pagination controls use dark text hierarchy
- [ ] Records data still loads, paginates, and filters correctly
- [ ] `pnpm build` completes without errors
