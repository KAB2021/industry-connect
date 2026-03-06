---
id: task-3.1
title: Reskin DashboardPage
complexity: medium
method: refactor
blocked_by: [task-2.1]
blocks: []
files: [frontend/src/pages/DashboardPage.tsx]
standards: []
---

## Description
Apply the Midnight Neon theme to the Dashboard page. Update the inline `StatCard` component and page-level styling to use glassmorphism cards, the gradient hero card, and dark text hierarchy.

## Actions
1. Update `StatCard` base styling: replace `bg-white rounded-lg border border-gray-200 shadow-sm` with `bg-surface border border-border backdrop-blur-md rounded-xl hover:border-border-hover transition-colors`.
2. Make the first stat card (Total Records) use the gradient hero treatment: `bg-linear-135/srgb from-primary to-secondary` background with `border-border-accent`.
3. Update text colours: heading `text-2xl font-bold text-gray-900` becomes `text-2xl font-bold text-text-primary`. Subtext/labels use `text-text-secondary` or `text-text-muted` per hierarchy.
4. Update grid gap and any remaining light-mode utility classes (`bg-gray-*`, `text-gray-*`).

## Acceptance
- [ ] All stat cards show glassmorphism styling with hover border effect
- [ ] First stat card (Total Records) has cyan-emerald gradient background
- [ ] Text hierarchy uses the 4-level zinc scale
- [ ] Dashboard data still loads and displays correctly
- [ ] `pnpm build` completes without errors
