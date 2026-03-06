---
id: task-2.1
title: Restructure AppLayout to sidebar and topbar
complexity: high
method: refactor
blocked_by: [task-1.1]
blocks: [task-3.1, task-3.2, task-3.3, task-3.4]
files: [frontend/src/layouts/AppLayout.tsx]
standards: []
---

## Description
Replace the horizontal top navigation bar with a fixed 60px icon-only sidebar on the left and a sticky frosted-glass topbar above the content area. The `<Outlet />` router integration stays unchanged. The layout wraps the entire app and must apply the dark background + ambient glow.

## Actions
1. Change the outer wrapper from `min-h-screen bg-gray-50` to `min-h-screen bg-bg ambient-glow flex`.
2. Build the sidebar as a fixed `w-[60px] h-screen` flex column:
   - Top: gradient logo badge (inline SVG) with `shadow-glow` and `rounded-xl`
   - Middle: four nav icons (Dashboard, Records, Upload, Analysis) using inline SVGs with `currentColor`. Each is a `NavLink` — active state applies `bg-sidebar-active` + a 3px left border using the cyan-emerald gradient.
   - Bottom: user avatar circle (placeholder `div` with initials).
3. Build the topbar as a sticky `top-0` element inside the content area:
   - Frosted glass: `bg-surface backdrop-blur-lg border-b border-border`
   - Left: current page title (derive from route or pass as context)
   - Right: search placeholder input (visual only, no functionality)
4. Content area: `flex-1 ml-[60px]` with `<Outlet />` below the topbar, padded per design brief (28px vertical, 32px horizontal).
5. Responsive fallback: on screens < 768px, hide the sidebar and let content go full-width. Use Tailwind responsive prefixes (`hidden md:flex` on sidebar, remove `ml-[60px]` on small screens).

## Edge Cases
- `NavLink` active detection must work with the existing route paths — do not change routing
- Page title in topbar should update when navigating between pages
- Sidebar must not scroll with content (use `fixed` or `sticky` with `h-screen`)

## Acceptance
- [ ] Sidebar is fixed at 60px, visible on desktop, hidden on mobile
- [ ] Logo badge displays gradient background with glow shadow
- [ ] Four nav icons render and link to correct routes
- [ ] Active nav item shows cyan background + left accent bar
- [ ] Topbar is sticky with frosted glass effect and shows page title
- [ ] `<Outlet />` renders page content correctly
- [ ] All existing routes still work (/, /records, /upload, /analysis)
- [ ] `pnpm build` completes without errors
