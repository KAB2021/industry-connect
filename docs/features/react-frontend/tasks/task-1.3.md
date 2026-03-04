---
id: task-1.3
title: Scaffold React + Vite + Tailwind CSS project
complexity: medium
method: write-test
blocked_by: []
blocks: [task-1.4, task-2.1]
files: [frontend/]
standards: []
---

## Description
Scaffold a new React + TypeScript project using `create-vite` with the `react-ts` template in a `frontend/` directory at the project root. Install and configure Tailwind CSS v4 with the `@tailwindcss/vite` plugin. Configure Vite's dev server proxy to forward API requests to `http://localhost:8000`. Set up `VITE_API_BASE_URL` and `VITE_POLL_INTERVAL_MS` environment variables.

## Actions
1. Run `npm create vite@latest frontend -- --template react-ts` from the project root
2. Install Tailwind CSS v4: `npm install tailwindcss @tailwindcss/vite` in `frontend/`
3. Add `@tailwindcss/vite` plugin to `vite.config.ts`
4. Replace default CSS with Tailwind's `@import "tailwindcss"` in the main CSS file
5. Configure `server.proxy` in `vite.config.ts` to forward `/upload`, `/webhook`, `/records`, `/analyse`, `/health` to `http://localhost:8000`
6. Add `VITE_API_BASE_URL` (default empty string for proxy mode) and `VITE_POLL_INTERVAL_MS` (default `30000`) env var usage
7. Remove Vite boilerplate (default App component content, logos, counter)
8. Verify `npm run dev` starts and `npm run build` produces `dist/` with static assets

## Acceptance
- [ ] `frontend/` directory exists with React + TypeScript + Vite
- [ ] Tailwind CSS v4 classes render correctly in the browser
- [ ] `npm run build` in `frontend/` produces static assets in `frontend/dist/`
- [ ] Vite dev server proxies API requests to `localhost:8000`
- [ ] `VITE_API_BASE_URL` and `VITE_POLL_INTERVAL_MS` env vars are configured
