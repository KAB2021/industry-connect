---
id: task-2.1
title: Set up React Router and app layout with navigation
complexity: medium
method: write-test
blocked_by: [task-1.3]
blocks: [task-3.1, task-3.2, task-3.3, task-3.4]
files: [frontend/src/App.tsx, frontend/src/layouts/AppLayout.tsx, frontend/src/pages/]
standards: []
---

## Description
Install React Router v7 and configure client-side routing with 4 routes: `/` (Dashboard), `/records` (Records), `/upload` (Upload), `/analysis` (Analysis). Create a shared `AppLayout` component with a persistent top navigation bar containing links to all 4 views. Each route renders a placeholder component initially.

## Actions
1. Install `react-router` in `frontend/`
2. Create `frontend/src/layouts/AppLayout.tsx` — a layout component with a top nav bar (`<nav>`) containing `<NavLink>` elements for Dashboard, Records, Upload, Analysis, and an `<Outlet>` for route content
3. Create placeholder page components in `frontend/src/pages/`: `DashboardPage.tsx`, `RecordsPage.tsx`, `UploadPage.tsx`, `AnalysisPage.tsx`
4. Configure routes in `frontend/src/App.tsx` using `createBrowserRouter` with the `AppLayout` as the parent route and the 4 pages as children
5. Style the nav bar with Tailwind CSS — clean, minimal, with active link highlighting

## Acceptance
- [ ] Navigating between views does not cause a full page reload
- [ ] All 4 routes render their respective placeholder pages
- [ ] The nav bar is visible on all views with active link highlighting
- [ ] Navigating to `/` renders the Dashboard placeholder
