---
id: task-4.1
title: Add frontend Docker service and update docker-compose
complexity: medium
method: write-test
blocked_by: [task-1.2, task-3.1, task-3.2, task-3.3, task-3.4]
blocks: []
files: [frontend/Dockerfile, docker-compose.yml, frontend/nginx.conf]
standards: []
---

## Description
Create a multi-stage Dockerfile for the frontend (Node build stage → nginx serve stage) and add a `frontend` service to `docker-compose.yml`. The nginx container serves the static build and proxies API requests to the backend service.

## Actions
1. Create `frontend/Dockerfile`:
   - Stage 1 (build): `node:20-alpine`, install deps, `npm run build`
   - Stage 2 (serve): `nginx:alpine`, copy `dist/` to nginx html dir, copy custom `nginx.conf`
2. Create `frontend/nginx.conf`:
   - Serve static files from `/usr/share/nginx/html`
   - Proxy `/upload`, `/webhook`, `/records`, `/analyse`, `/health`, `/docs`, `/openapi.json` to `http://app:8000`
   - Handle SPA routing: `try_files $uri $uri/ /index.html`
3. Add `frontend` service to `docker-compose.yml`:
   - Build from `frontend/Dockerfile`
   - Port `3000:80`
   - Depends on `app` service
4. Set `VITE_API_BASE_URL` as empty string in the Docker build (nginx handles proxying)

## Acceptance
- [ ] `docker-compose up` builds and starts the frontend service
- [ ] Frontend is accessible at `http://localhost:3000`
- [ ] API requests from the frontend are proxied to the backend via nginx
- [ ] SPA routing works (refreshing on `/records` serves the app, not 404)
