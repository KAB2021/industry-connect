---
id: task-1.1
title: Add CORS middleware to FastAPI backend
complexity: low
method: write-test
blocked_by: []
blocks: []
files: [app/main.py, app/config.py, .env.example]
standards: []
---

Add `CORSMiddleware` to the FastAPI app in `app/main.py` to allow cross-origin requests from the frontend. Add a `CORS_ALLOWED_ORIGINS` env var to `app/config.py` (default `"http://localhost:5173"` for Vite dev server). Add the new var to `.env.example`.

## Actions
1. Add `CORS_ALLOWED_ORIGINS: str = "http://localhost:5173"` to the `Settings` class in `app/config.py`
2. In `app/main.py`, import `CORSMiddleware` from `fastapi.middleware.cors` and add `app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ALLOWED_ORIGINS.split(","), allow_methods=["*"], allow_headers=["*"])` after the app is created
3. Add `CORS_ALLOWED_ORIGINS=http://localhost:5173` to `.env.example`

## Acceptance
- [ ] Backend responds with `Access-Control-Allow-Origin` header on preflight OPTIONS requests
- [ ] `CORS_ALLOWED_ORIGINS` is configurable via environment variable
