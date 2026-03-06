---
id: task-3.3
title: Reskin UploadPage
complexity: medium
method: refactor
blocked_by: [task-2.1]
blocks: []
files: [frontend/src/pages/UploadPage.tsx]
standards: []
---

## Description
Apply the Midnight Neon theme to the Upload page. Update the form card, drag zone, file input pseudo-element styling, and primary action button.

## Actions
1. Replace form card `bg-white border border-gray-200 rounded-lg` with `bg-surface border border-border backdrop-blur-md rounded-xl`.
2. Update drag zone border: dashed border transitions to cyan accent on hover (`hover:border-primary`) with subtle cyan background tint (`hover:bg-sidebar-active`).
3. Replace file input pseudo-element classes `file:bg-blue-50 file:text-blue-700` with dark variants: `file:bg-white/5 file:text-primary-light`.
4. Replace primary button `bg-blue-600` with gradient button: `bg-linear-135/srgb from-primary to-secondary text-white shadow-glow hover:shadow-glow-hover transition-shadow`.
5. Update all text colours to the 4-level hierarchy. Labels `text-text-muted`, body `text-text-secondary`, headings `text-text-primary`.

## Edge Cases
- `file:` pseudo-element classes with dark theme tokens — verify these render correctly in Tailwind v4 (uncommon pattern per research risk #2)

## Acceptance
- [ ] Form card shows glassmorphism styling
- [ ] Drag zone border transitions to cyan on hover with subtle background tint
- [ ] File input pseudo-element uses dark styling
- [ ] Upload button uses gradient + glow shadow that intensifies on hover
- [ ] Upload functionality still works (file selection, upload trigger, progress)
- [ ] `pnpm build` completes without errors
