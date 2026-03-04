---
feature: react-frontend
type: decisions
created: 2026-03-04T00:00:00Z
---

# Technical Decisions: React Frontend

## Decision 1: Client-Side Routing Library

### Options
| Option | Pros | Cons |
|--------|------|------|
| React Router v7 (SPA mode) | Mature, widely adopted, simpler API for basic routing, extensive docs and community support | Limited type safety in SPA mode (enhanced features only in framework mode) |
| TanStack Router | TypeScript-first with automatic type inference for routes/params/search, catches routing errors at compile time | Steeper initial setup, smaller community, newer ecosystem |

### Recommendation
React Router v7 — this is a 4-view SPA with no complex route parameters or nested search params. The type safety advantage of TanStack Router doesn't justify the learning curve for this scope. React Router's SPA mode is well-documented and sufficient.

## Decision 2: Data Fetching Strategy

### Options
| Option | Pros | Cons |
|--------|------|------|
| TanStack Query (React Query) | Built-in `refetchInterval` for auto-polling, caching, deduplication, loading/error state management, `useMutation` for POST operations, stale-while-revalidate | Additional dependency (~13kb), learning curve for query keys and cache invalidation |
| Manual `useState` + `useEffect` + `fetch` | Zero dependencies, full control, simpler mental model | Boilerplate for every endpoint (loading, error, data states), manual cleanup for race conditions, no caching, manual polling implementation with `setInterval` |

### Recommendation
TanStack Query — the auto-polling requirement (`refetchInterval`), multi-endpoint data fetching (records, analysis), and mutation handling (upload, analyse) map directly to TanStack Query's API. Manual implementation would require reimplementing most of what TanStack Query provides. The bundle cost is minimal relative to the boilerplate eliminated.

## Decision 3: HTTP Client

### Options
| Option | Pros | Cons |
|--------|------|------|
| Native `fetch` API | Zero bundle cost, native to all modern browsers, supports `FormData` for file uploads | No built-in upload progress tracking, more verbose error handling (must check `response.ok` manually), no interceptors |
| Axios | Built-in progress tracking, interceptors, automatic JSON parsing, cleaner error handling | ~35kb bundle addition, upload progress not required by spec |

### Recommendation
Native `fetch` — the spec does not require upload progress indicators. `fetch` with `FormData` handles CSV uploads. A thin wrapper function can standardize error handling (check status codes, parse JSON/detail shapes). Axios's bundle cost is not justified for this use case.

## Decision 4: Table Implementation

### Options
| Option | Pros | Cons |
|--------|------|------|
| TanStack Table | Powerful headless hooks for sorting, filtering, pagination; extensible; handles complex table state | Headless — all UI built manually, ~15kb, client-side pagination may conflict with server-side `limit/offset`, overkill for 7 columns |
| Manual table (Array.sort/filter + HTML table) | Simple, zero dependencies, direct control over server-side pagination via `limit/offset` params, easy to understand | More code for sort/filter logic, no built-in column resizing or virtualization |

### Recommendation
Manual table — the records table has 7 columns with client-side sorting and filtering over the loaded page of records. Server-side pagination is already handled by `GET /records?limit=N&offset=N`. TanStack Table's client-side pagination model would need to be wired into "manual" mode to work with the server-side API, adding complexity without benefit. A simple implementation with `Array.sort()`, `Array.filter()`, and pagination buttons that adjust `offset` is clearer and sufficient.

## Decision 5: Development vs. Production Serving Strategy

### Options
| Option | Pros | Cons |
|--------|------|------|
| Standalone dev server (Vite on host) + Docker service for production | Fast HMR on macOS (no Docker volume mount overhead), simple `npm run dev` workflow, Docker service uses multi-stage build (Node → nginx) for production | Requires CORS on backend OR Vite proxy config during dev, two different serving models to maintain |
| Docker service for both dev and production | Consistent environment, single `docker-compose up` starts everything | Vite HMR slow on macOS due to Docker volume mount inotify limitations, more complex docker-compose config for dev mode, rebuilds on every file change |
| FastAPI static mount (serve frontend from backend) | No CORS needed (same origin), single service | Couples frontend to backend deployment, complicates frontend development workflow, backend must rebuild/restart for frontend changes |

### Recommendation
Standalone dev server + Docker for production — use Vite's `server.proxy` in `vite.config.ts` to forward API requests to `localhost:8000` during development (eliminates CORS during dev). For production, add a `frontend` service to `docker-compose.yml` with a multi-stage Dockerfile (Node build → nginx serve). CORS middleware is still needed on the backend for production since the frontend and backend will be on different origins/ports.
