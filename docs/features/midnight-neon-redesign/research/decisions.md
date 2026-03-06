---
feature: midnight-neon-redesign
type: decisions
created: 2026-03-05
---

# Technical Decisions: Midnight Neon Redesign

## Decision 1: Design Token Strategy

### Options
| Option | Pros | Cons |
|--------|------|------|
| A: `@theme` with direct values | Simple, one block in `index.css`, auto-generates all utilities | No runtime CSS variable access for future theming; harder to swap palettes later |
| B: `:root` vars + `@theme inline` | Runtime CSS variables for future theme switching; tokens accessible in plain CSS too | More verbose (two blocks); `inline` keyword gotcha; `@theme inline` doesn't emit its own CSS vars |
| C: Hardcoded arbitrary values in JSX | No CSS changes needed; fast to write | No centralisation; 20+ colour values scattered across 8 files; painful to change later |

### Recommendation
**Option A: `@theme` with direct values.** The feature spec explicitly excludes a dark/light toggle. Direct `@theme` values are simpler, avoid the `inline` gotcha, and still centralise all tokens in one place. If theming is added later, migrating from `@theme` to `@theme inline` + `:root` is a small, mechanical change.

## Decision 2: Ambient Glow Implementation

### Options
| Option | Pros | Cons |
|--------|------|------|
| A: Plain CSS class in `index.css` | Readable, multi-line radial gradients easy to author, can use `background-attachment: fixed` | One non-utility class in an otherwise utility-only codebase |
| B: Tailwind arbitrary value on a wrapper div | Everything stays as utilities | Extremely long, unreadable class string for multi-orb radials |
| C: Inline `style` attribute in JSX | No CSS file changes | Not reusable, verbose, violates the Tailwind-first pattern |

### Recommendation
**Option A: Plain CSS class.** A single `.ambient-glow` class with `background-attachment: fixed` applied to the `<body>` or root wrapper. The multi-orb radial gradient is impractical as a Tailwind arbitrary value. One utility-exception is acceptable.

## Decision 3: Gradient Colour Interpolation

### Options
| Option | Pros | Cons |
|--------|------|------|
| A: Default oklab | Perceptually smoother gradient; Tailwind v4 default | Midpoint colours differ slightly from sRGB mockup |
| B: Force sRGB via `/srgb` | Exact match to mockup gradient | Slightly less perceptually smooth; requires modifier on every gradient usage |

### Recommendation
**Option B: Force sRGB.** The mockup is the build spec. Use `bg-linear-135/srgb` to ensure gradients match exactly. The visual difference is subtle but consistency with the approved design matters.
