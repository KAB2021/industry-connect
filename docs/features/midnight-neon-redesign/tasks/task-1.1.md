---
id: task-1.1
title: Define design tokens and ambient glow CSS
complexity: medium
method: write-test
blocked_by: []
blocks: [task-2.1, task-3.1, task-3.2, task-3.3, task-3.4]
files: [frontend/src/index.css]
standards: []
---

## Description
Replace the bare `@import "tailwindcss"` in `index.css` with a full `@theme` block defining all Midnight Neon design tokens, plus a `.ambient-glow` utility class for the background radial gradients. This establishes the colour system, shadow tokens, and utility classes consumed by every other task.

## Actions
1. Add a `@theme` block after the Tailwind import with direct values (Decision 1: Option A). Define tokens for:
   - `--color-bg: #080C14` (page background)
   - `--color-surface: rgba(255,255,255,0.03)` (glass card bg)
   - `--color-border: rgba(255,255,255,0.06)` (card/table borders)
   - `--color-border-hover: rgba(255,255,255,0.1)` (hover border)
   - `--color-border-accent: rgba(6,182,212,0.2)` (accent card border)
   - `--color-primary: #06B6D4` (cyan)
   - `--color-primary-light: #22D3EE` (cyan-400)
   - `--color-secondary: #10B981` (emerald)
   - `--color-text-primary: #F4F4F5` (headings/values)
   - `--color-text-secondary: #A1A1AA` (body)
   - `--color-text-muted: #71717A` (labels)
   - `--color-text-faint: #52525B` (timestamps)
   - `--color-sidebar-active: rgba(6,182,212,0.12)` (active nav item bg)
   - `--color-success: #10B981`, `--color-success-bg: rgba(16,185,129,0.1)`
   - `--color-warning: #F59E0B`, `--color-warning-bg: rgba(245,158,11,0.1)`
   - `--color-danger: #EF4444`, `--color-danger-bg: rgba(239,68,68,0.1)`
   - `--shadow-glow: 0 0 16px rgba(6,182,212,0.15)` (button glow)
   - `--shadow-glow-hover: 0 0 24px rgba(6,182,212,0.25)` (button glow on hover)
2. Add a `.ambient-glow` class using plain CSS with `background-attachment: fixed` and multi-orb radial gradients (cyan at 6% opacity, emerald at 4% opacity) per Decision 2: Option A.
3. Reset Tailwind default colour palette if needed: `--color-*: initial` inside `@theme` to avoid conflicts with default Tailwind colours leaking through.

## Edge Cases
- Do NOT define tokens using `rgba()` and then stack Tailwind opacity modifiers on them (e.g. `bg-surface/50`) — this compounds opacity via `color-mix`. Document this in a CSS comment next to the token block.
- Use `/srgb` gradient interpolation per Decision 3 when defining any gradient references in comments/docs.

## Acceptance
- [ ] `@theme` block defines all 20+ tokens listed above
- [ ] `bg-surface`, `text-text-primary`, `border-border`, `shadow-glow` etc. are usable as Tailwind utilities
- [ ] `.ambient-glow` class produces visible radial gradient orbs on `#080C14` background
- [ ] `npm run build` (or `pnpm build`) completes without CSS errors
