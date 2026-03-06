---
name: industryconnect-redesign
type: dashboard
created: 2026-03-05
status: draft
---

# Design Brief: IndustryConnect Redesign

## Direction
Midnight Neon — a dark glassmorphism dashboard with cyan/emerald gradient accents on a deep navy base. Subtle ambient glow effects, frosted glass cards, and a compact icon sidebar. Clean, data-focused, with a refined sci-fi edge. Inspired by trending Figma community dark dashboards and the dark glassmorphism aesthetic.

## Color Palette
- Primary: `#06B6D4` (cyan-500) — buttons, active states, accent gradient start
- Primary Light: `#22D3EE` (cyan-400) — active sidebar items, badge text, highlighted values
- Secondary: `#10B981` (emerald-500) — accent gradient end, success states
- Accent Gradient: `linear-gradient(135deg, #06B6D4, #10B981)` — logo, primary buttons, progress bars
- Background: `#080C14` (deep navy) — page canvas
- Ambient Glow: `radial-gradient` of cyan at 6% opacity + emerald at 4% opacity — background depth
- Surface (Glass): `rgba(255,255,255,0.03)` — card backgrounds with `backdrop-filter: blur(12px)`
- Border: `rgba(255,255,255,0.06)` — card/table borders
- Border Accent: `rgba(6,182,212,0.2)` — accent card borders
- Text Primary: `#F4F4F5` (zinc-100) — headings, values
- Text Secondary: `#A1A1AA` (zinc-400) — body text, table cells
- Text Muted: `#71717A` (zinc-500) — labels, descriptions
- Text Faint: `#52525B` (zinc-600) — timestamps, metadata
- Semantic Warning: `#F59E0B` / bg `rgba(245,158,11,0.1)` — anomalies, pending badges
- Semantic Success: `#10B981` / bg `rgba(16,185,129,0.1)` — analysed badges
- Semantic Danger: `#EF4444` / bg `rgba(239,68,68,0.1)` — errors

## Typography
- Font: Inter (with system fallbacks)
- Page title: 22px / 700 weight
- Section title: 15px / 600 weight
- Stat value: 32px / 800 weight, -1px letter-spacing
- Body: 13-13.5px / 400-500 weight
- Labels: 10-11px / 600 weight, uppercase, 0.5-0.6px letter-spacing
- Monospace (IDs): SF Mono / Cascadia Code, 12px

## Layout
- Fixed icon sidebar (60px wide) on the left — logo top, avatar bottom
- Sticky topbar with frosted glass effect (`backdrop-filter: blur(16px)`) — page title + search
- Active sidebar item has a cyan left-edge indicator bar
- Max content width: 1100px
- Content padding: 28px vertical, 32px horizontal
- Stats grid: 3-column, 14px gap
- Card border-radius: 12px, buttons: 8px
- Spacing scale: 4/6/8/12/14/16/20/24/28/32px

## Key Design Techniques

### Glassmorphism
- Cards use `rgba(255,255,255,0.03)` background + `backdrop-filter: blur(12px)`
- Thin semi-transparent white borders (`rgba(255,255,255,0.06)`)
- Hover state brightens border to `rgba(255,255,255,0.1)`

### Ambient Glow
- Background uses fixed `radial-gradient` orbs of cyan and emerald at very low opacity
- Primary button has `box-shadow: 0 0 16px rgba(6,182,212,0.15)`, intensifies on hover

### Dark Mode Text Hierarchy
- No pure white — brightest text is `#F4F4F5`
- 4-level hierarchy: F4F4F5 > A1A1AA > 71717A > 52525B

## Components

### Sidebar
- 60px fixed, icon-only navigation
- Gradient logo badge with glow shadow
- Active item: cyan glow background + 3px left accent bar
- Avatar circle at bottom

### Stat Cards
- Glass cards with hover border lift
- First card uses cyan/emerald gradient background + accent border (the hero metric)
- Progress bars with gradient fill

### Data Table (Records)
- Glass container, tight rows
- Source filter chips (pill-shaped, cyan active state with glow background)
- Sortable columns with directional arrows
- Status badges: green "Analysed", amber "Pending"
- Monospace entity IDs

### Upload Zone
- Dashed border, transitions to cyan accent border + subtle cyan background on hover
- Cyan glow icon container
- File preview card with gradient upload button

### Analysis Result Cards
- Glass cards with section dividers
- Anomaly items: amber semi-transparent background with metric badges
- Token badges: cyan for prompt, muted for completion
- Record ID chips in monospace

### Trigger Card
- Horizontal glass card with info + gradient CTA button
- Glow effect on button hover

## References
- [Glassmorphism Dashboard UI Kit](https://www.figma.com/community/file/1514405085901665002) — Apple Liquid Glass-inspired frosted cards
- [Multiple Dark Dashboards](https://www.figma.com/community/file/1354429309780258770) — Dark layout patterns and color usage
- [Operations Dashboard Dark Mode](https://www.figma.com/community/file/1506487400738812731) — Data-driven dark UI for operations
- [Data Dashboard Glass Bento UI](https://www.figma.com/community/file/1320413003375217236) — Glass bento grid system
- [Dark Glassmorphism: The Aesthetic That Will Define UI in 2026](https://medium.com/@developer_89726/dark-glassmorphism-the-aesthetic-that-will-define-ui-in-2026-93aa4153088f) — Ambient gradients + backdrop blur techniques
