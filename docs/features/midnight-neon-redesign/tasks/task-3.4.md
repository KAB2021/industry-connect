---
id: task-3.4
title: Reskin AnalysisPage and AnalysisResultCard
complexity: high
method: refactor
blocked_by: [task-2.1]
blocks: []
files: [frontend/src/pages/AnalysisPage.tsx, frontend/src/components/AnalysisResultCard.tsx]
standards: []
---

## Description
Apply the Midnight Neon theme to the Analysis page and its shared `AnalysisResultCard` component. This covers the trigger card, primary action button, result cards, anomaly rows, token badges, and error/empty states.

## Actions
1. **AnalysisPage.tsx — Trigger card:** Replace light card styling with glass card (`bg-surface border border-border backdrop-blur-md rounded-xl`). Replace `bg-indigo-600` button with gradient button: `bg-linear-135/srgb from-primary to-secondary text-white shadow-glow hover:shadow-glow-hover`.
2. **AnalysisPage.tsx — States:** Update error states and empty states from light grays to dark theme tokens. Error text uses `text-danger`, empty state text uses `text-text-muted`.
3. **AnalysisResultCard.tsx — Card wrapper:** Apply glassmorphism styling with hover border effect.
4. **AnalysisResultCard.tsx — Anomaly rows:** Replace `bg-yellow-50 border-yellow-200` with `bg-warning-bg border-warning/20`.
5. **AnalysisResultCard.tsx — Token badges:** Replace prompt `bg-blue-50 text-blue-700` with `bg-primary/10 text-primary-light`. Replace completion `bg-purple-50 text-purple-700` with `bg-white/5 text-text-muted`.
6. **AnalysisResultCard.tsx — Record IDs:** Replace `font-mono bg-gray-100` with `font-mono bg-white/5 text-text-secondary`.
7. **AnalysisResultCard.tsx — Expand link:** Replace `text-blue-600` with `text-primary-light hover:text-primary`.
8. Update all remaining light-mode text classes to the 4-level hierarchy.

## Edge Cases
- The trigger card and result cards coexist on the same page — ensure consistent glass treatment
- Auto-polling for analysis results must continue to work after reskin

## Acceptance
- [ ] Trigger card shows glassmorphism styling with gradient CTA button
- [ ] Result cards show glassmorphism with hover border effect
- [ ] Anomaly rows use amber semi-transparent background
- [ ] Token badges use cyan (prompt) and muted (completion) colours
- [ ] Record ID chips use monospace with dark background
- [ ] Error and empty states use dark theme colours
- [ ] Analysis trigger, auto-polling, and result display still work
- [ ] `pnpm build` completes without errors
