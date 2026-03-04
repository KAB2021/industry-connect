---
id: task-1.2
title: Create .dockerignore to exclude frontend build artifacts
complexity: low
method: write-test
blocked_by: []
blocks: [task-4.1]
files: [.dockerignore]
standards: []
---

Create a `.dockerignore` file at the project root to prevent `frontend/node_modules/`, `frontend/dist/`, and other non-backend files from being copied into the backend Docker image via `COPY . .` in the Dockerfile.

Acceptance: `.dockerignore` exists and excludes `frontend/node_modules`, `frontend/dist`, `frontend/.cache`, `.git`, `__pycache__`, `.env`
