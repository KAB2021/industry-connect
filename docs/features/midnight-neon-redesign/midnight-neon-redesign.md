---
id: feat-aa2074eb
title: Midnight Neon Redesign
status: complete
created: 2026-03-05T00:00:00Z
---

# Midnight Neon Redesign

## Overview

The frontend is reskinned from its current generic light-mode Tailwind styling to a dark glassmorphism "Midnight Neon" theme. The layout changes from a top navigation bar to a fixed icon-only sidebar (60px) on the left, with a sticky frosted-glass topbar showing the current page title and a search placeholder. All four existing pages (Dashboard, Records, Upload, Analysis) retain their current functionality but receive updated visual treatment.

The colour scheme shifts to a deep navy base (`#080C14`) with cyan-to-emerald gradient accents (`#06B6D4` to `#10B981`). Cards use semi-transparent white backgrounds (`rgba(255,255,255,0.03)`) with `backdrop-filter: blur(12px)` to create a frosted glass effect. Subtle radial gradient "ambient glow" orbs of cyan and emerald sit behind the content at low opacity to add depth. Text hierarchy uses four zinc shades (F4F4F5, A1A1AA, 71717A, 52525B) instead of pure white to reduce eye strain.

The sidebar features a gradient logo badge with a glow shadow, icon-only navigation items with a cyan left-edge active indicator, and a user avatar at the bottom. Interactive elements (buttons, chips, cards) have hover states that brighten borders or intensify glow shadows. The primary action button uses the cyan-emerald gradient with a `box-shadow` glow that intensifies on hover. Semantic colours are preserved: green for success/analysed, amber for warnings/pending/anomalies, red for errors.

The approved mockup at `docs/designs/industryconnect-redesign/mockup.html` and the design brief at `docs/designs/industryconnect-redesign/design-brief.md` are the visual specification. The implementation must match the mockup's appearance across all four pages.

## Success Criteria

- [ ] The app background is dark (`#080C14`) with ambient radial gradient glow effects visible behind content.
- [ ] Navigation uses a fixed 60px icon-only sidebar on the left with: gradient logo badge at top, four page icons, user avatar at bottom.
- [ ] The active sidebar item displays a cyan-tinted background (`rgba(6,182,212,0.12)`) and a 3px left-edge accent bar using the cyan-emerald gradient.
- [ ] A sticky topbar sits above the content area with frosted glass effect (`backdrop-filter: blur(16px)`) showing the current page title and a search placeholder.
- [ ] All cards use glassmorphism styling: `rgba(255,255,255,0.03)` background, `rgba(255,255,255,0.06)` border, `backdrop-filter: blur(12px)`.
- [ ] Card borders brighten to `rgba(255,255,255,0.1)` on hover.
- [ ] The Dashboard stat card for the primary metric (Total Records) uses a cyan-emerald gradient background with an accent border.
- [ ] The primary action button (Run Analysis, Upload) uses `linear-gradient(135deg, #06B6D4, #10B981)` with a glow `box-shadow` that intensifies on hover.
- [ ] Text hierarchy uses exactly four levels: `#F4F4F5` for headings/values, `#A1A1AA` for body text, `#71717A` for labels, `#52525B` for timestamps/metadata.
- [ ] Filter chips on the Records page use a cyan glow active state matching the mockup.
- [ ] Status badges use semantic colours: green (`rgba(16,185,129,0.1)`) for "Analysed", amber (`rgba(245,158,11,0.1)`) for "Pending", red (`rgba(239,68,68,0.1)`) for errors.
- [ ] The Upload page drag zone border transitions to cyan accent colour on hover with a subtle cyan background tint.
- [ ] All existing functionality from the react-frontend feature continues to work: routing, API calls, pagination, upload, analysis trigger, auto-polling, error handling.
- [ ] Edge case: the app remains readable when `backdrop-filter` is unsupported (cards should still have a visible background via the `rgba` fallback).

## Scope

**IN:**
- Complete visual reskin of all four pages (Dashboard, Records, Upload, Analysis)
- Layout restructure: top nav replaced by fixed icon sidebar + sticky topbar
- CSS custom properties (design tokens) for all colours, borders, radii, and spacing
- Dark glassmorphism card styling with backdrop blur
- Ambient background glow gradients
- Gradient accent buttons with glow hover effect
- Updated stat cards, table styling, filter chips, badges, alerts, upload zone, analysis result cards
- Sidebar active state with left-edge indicator
- Responsive fallback: sidebar collapses/hides on mobile, content goes full-width

**OUT:**
- Dark/light mode toggle (dark mode only for now — deferred)
- New functionality beyond visual changes (no new API calls, no new features)
- Icon library addition (use inline SVGs matching the mockup)
- Animation or transition beyond hover states (deferred — keep it snappy)
- Component library extraction or design system package (premature for this scope)
- Search functionality behind the topbar search placeholder (visual only for now)

## Implementation Notes

**Approach:** Tailwind CSS v4 `@theme` directive with CSS custom properties that auto-generate utility classes (`bg-surface`, `text-text-primary`, etc.). This hybrid approach keeps JSX using Tailwind utilities while centralising all design tokens in `index.css`.

**Files changed (8):**
- `frontend/src/index.css` — Design tokens via `@theme`, ambient glow class, `html` background
- `frontend/src/layouts/AppLayout.tsx` — Fixed 60px sidebar, expandable search, click-outside collapse
- `frontend/src/pages/DashboardPage.tsx` — Glassmorphism stat cards, gradient hero card
- `frontend/src/pages/RecordsPage.tsx` — Dark pagination controls
- `frontend/src/pages/UploadPage.tsx` — Drag-and-drop upload zone with cyan hover
- `frontend/src/pages/AnalysisPage.tsx` — Glass trigger card, gradient CTA button
- `frontend/src/components/RecordsTable.tsx` — Filter chips, row striping, status badges
- `frontend/src/components/AnalysisResultCard.tsx` — Result cards, anomaly rows, token badges

**Deviations from spec:**
1. **Topbar removed** — Replaced by expandable sidebar search (click search icon → sidebar widens to 240px with search input, click outside to collapse). User-directed change.
2. **Upload zone** — Rebuilt from standard file input to full drag-and-drop zone matching the mockup (dashed border, upload icon, cyan hover transition).

**Open question resolved:** Used the `@theme` + utility class hybrid approach — tokens in CSS, consumption via Tailwind classes in JSX.
