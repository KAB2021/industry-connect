---
feature: midnight-neon-redesign
type: research
created: 2026-03-05
---

# Research: Midnight Neon Redesign

## Relevant Code

### Layout (must restructure)
- `frontend/src/layouts/AppLayout.tsx` — Top nav bar with horizontal `NavLink` items. Outer wrapper `min-h-screen bg-gray-50`, nav uses `max-w-7xl mx-auto`. Must become flex row with fixed 60px sidebar + fluid content area. Router uses `<Outlet />` — only this file needs structural changes; no routing changes required.

### Pages (colour reskin, 4 files)
- `frontend/src/pages/DashboardPage.tsx` — Inline `StatCard` component: `bg-white rounded-lg border border-gray-200 shadow-sm p-6`. Heading `text-2xl font-bold text-gray-900`. Grid `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`.
- `frontend/src/pages/RecordsPage.tsx` — Secondary buttons `border border-gray-300 bg-white`. Pagination `text-sm text-gray-500`.
- `frontend/src/pages/UploadPage.tsx` — Form card `bg-white border border-gray-200 rounded-lg`. Primary button `bg-blue-600`. File input `file:bg-blue-50 file:text-blue-700`.
- `frontend/src/pages/AnalysisPage.tsx` — Primary button `bg-indigo-600` (inconsistent with Upload's `bg-blue-600`). Trigger card, error/empty states use light grays.

### Shared Components (colour reskin, 2 files)
- `frontend/src/components/RecordsTable.tsx` — Active filter chip `bg-blue-600 text-white`, inactive `bg-gray-100`. Table header `bg-gray-50`. **Row striping uses ternary:** `idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'` — must update the ternary values directly. Badges: `bg-green-100 text-green-800` (analysed), `bg-yellow-100 text-yellow-800` (pending).
- `frontend/src/components/AnalysisResultCard.tsx` — Anomaly rows `bg-yellow-50 border-yellow-200`. Token badges: prompt `bg-blue-50 text-blue-700`, completion `bg-purple-50 text-purple-700`. Record IDs `font-mono bg-gray-100`. Expand link `text-blue-600`.

### CSS Entry Point
- `frontend/src/index.css` — Contains only `@import "tailwindcss";`. No `@theme` block, no custom properties. Design tokens go here.
- `frontend/src/App.css` — Empty. Irrelevant.

### Files Requiring NO Changes
- All hooks (4 files), `api/client.ts`, `api/types.ts`, `App.tsx`, `main.tsx`, `vite.config.ts` — pure data/routing/build, zero styling.

**Total files to modify: 8** — `index.css`, `AppLayout.tsx`, 4 pages, 2 components.

## Patterns & Standards

### Tailwind v4 Theming (no config file)
- **v4.2.1** with `@tailwindcss/vite`. No `tailwind.config.js` exists. All customization via CSS `@theme` directive.
- Define tokens: `@theme { --color-surface: rgba(255,255,255,0.03); }` auto-generates `bg-surface`, `text-surface`, `border-surface`.
- For CSS variable indirection: `@theme inline { --color-bg: var(--bg); }` with `:root { --bg: #080C14; }`. The `inline` keyword is critical — without it, `var()` breaks Tailwind's `color-mix()` opacity system.
- Remove defaults: `--color-*: initial` inside `@theme`.

### Tailwind v4 Utility Mapping

| Design Spec CSS | Tailwind v4 Class | Notes |
|---|---|---|
| `backdrop-filter: blur(12px)` | `backdrop-blur-md` | Exact match |
| `backdrop-filter: blur(16px)` | `backdrop-blur-lg` | Exact match |
| `rgba(255,255,255,0.03)` | `bg-white/[3%]` or named `bg-surface` | Named token preferred |
| `rgba(255,255,255,0.06)` | `border-white/[6%]` or named `border-border` | Named token preferred |
| `linear-gradient(135deg, #06B6D4, #10B981)` | `bg-linear-135 from-[#06B6D4] to-[#10B981]` | Use `/srgb` for exact colour match |
| Custom glow `box-shadow` | Define `--shadow-glow` in `@theme`, use `shadow-glow` | Don't also apply `shadow-cyan-*` |
| Radial gradient ambient glow | Plain CSS class `.ambient-glow` | Multi-orb radials impractical as utilities |

### Existing Patterns to Preserve
- Tailwind utility classes directly in JSX (no CSS modules, no styled-components)
- Inline SVG icons with `currentColor` — auto-follow text colour changes
- `transition-colors` on interactive elements
- `disabled:opacity-*` and `disabled:cursor-not-allowed` on buttons

### Inconsistency Found
- Upload uses `bg-blue-600`, Analysis uses `bg-indigo-600`. Reskin unifies these under the cyan-emerald gradient.

## External Findings

### backdrop-filter Browser Support
- 92/100 compatibility score. Baseline web feature since September 2024.
- Chrome 76+, Firefox 104+, Safari 9+, Edge 17+. No `-webkit-` prefix needed (Lightning CSS handles it).
- **Fallback:** the `rgba` background on glass cards provides a visible surface without blur. No extra CSS needed.
- **Gotcha:** `backdrop-filter` has no effect on elements with fully opaque backgrounds. Must use semi-transparent background.

### Tailwind v4 Gradient Interpolation
- Default interpolation is **oklab** (perceptually uniform), may produce slightly different midpoint colours than the sRGB mockup.
- Force exact match: `bg-linear-135/srgb from-[#06B6D4] to-[#10B981]`.
- Source: [Tailwind CSS background-image docs](https://tailwindcss.com/docs/background-image)

### Sources
- [Tailwind v4 Theme Variables](https://tailwindcss.com/docs/theme)
- [Tailwind v4 backdrop-filter blur](https://tailwindcss.com/docs/backdrop-filter-blur)
- [Tailwind v4 background-image / gradients](https://tailwindcss.com/docs/background-image)
- [Tailwind v4 box-shadow](https://tailwindcss.com/docs/box-shadow)
- [Can I Use: CSS Backdrop Filter](https://caniuse.com/css-backdrop-filter)
- [GitHub Discussion #15600: Multi-theme with CSS variables](https://github.com/tailwindlabs/tailwindcss/discussions/15600)

## Risks

1. **Row striping ternary** (`RecordsTable.tsx:124`) — `idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'` must be updated in the ternary itself. Easy to miss during bulk class replacement. Low impact.

2. **`file:` pseudo-element classes** (`UploadPage.tsx:47-53`) — `file:bg-blue-50 file:text-blue-700` needs dark variants. Pattern `file:bg-white/5 file:text-cyan-400` should work in Tailwind v4 but is uncommon — verify during implementation.

3. **oklab gradient interpolation** — Default colour space may produce a slightly greener midpoint for cyan-to-emerald gradient vs sRGB mockup. Use `/srgb` modifier if exact match needed. Low impact.

4. **Opacity modifier stacking on rgba tokens** — If a `@theme` colour is defined as `rgba(255,255,255,0.03)` and you apply `/50` opacity modifier, it compounds (color-mix of the rgba at 50%). Don't stack modifiers on pre-alpha'd tokens. Medium impact if missed.

## Answers to Open Questions

**Q: Should CSS be implemented as Tailwind utility classes directly in JSX, or as a CSS file with custom properties?**

**A: Hybrid — `@theme` tokens + Tailwind utilities.** Define all 20+ design tokens as `--color-*`, `--shadow-*` in `index.css` inside a `@theme {}` block. This auto-generates utility classes (`bg-surface`, `text-primary`, `shadow-glow`) usable directly in JSX — matching the current Tailwind-in-JSX pattern. For ambient glow radials (impractical as utilities), add one plain CSS class. This centralizes colours without changing the authoring pattern.
