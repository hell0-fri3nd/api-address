# 06 — Security

## Scope

The brief does not ask for authentication, so there is none. Every endpoint is public. Do not add auth, API keys, or user accounts.

This is acceptable for the exam only. Before any real deployment, add authentication and put the API behind a gateway.

## Rules

### Input

- Validate every body, path, and query value with Pydantic schemas. No unvalidated `dict` or `Request.json()` in routes.
- Input schemas use `extra="forbid"`, so clients cannot set `id`, `created_at`, `updated_at`, or `deleted_at`.
- Every string has a maximum length. Every number has a range.
- Cap result sizes: `limit` ≤ 100, `distance_km` ≤ 20000.

### Rate limiting

- Every endpoint is rate limited. This is non-negotiable.
- The limit is per client IP, per HTTP method, per route: `GET /addresses` and `GET /addresses/nearby` have separate counters, and all ids share the `/addresses/{address_id}` counter.
- The limit comes from `RATE_LIMIT` (default `60/minute`).
- Over the limit: 429 problem (RFC 9457) with a `Retry-After` header in seconds. Requests that fail validation still count.
- Counters live in process memory. That is correct with the single Uvicorn worker in `02-architecture.md`; with more workers or instances, move the counters to shared storage (Redis).
- Behind a reverse proxy every client has the proxy's IP. Run Uvicorn with `--proxy-headers` and `--forwarded-allow-ips` set to the proxy, so the real client IP is used.

### Database

- Build queries with SQLAlchemy expressions only. Never format values into SQL strings (no f-strings, no `text()` with concatenation).
- Soft-deleted rows are never returned by any endpoint.
- Keep the database-level check constraints on coordinates as a second line of defence.

### Errors and logging

- Never return tracebacks, SQL, or file paths. Unhandled errors return a 500 problem (RFC 9457) with `detail` `Internal server error`.
- Validation `errors` items contain `loc`, `msg`, `type` only; they do not echo the submitted input.
- Run with `debug=False` and without `--reload` in Docker.
- Addresses are personal data. Uvicorn's access log is enough; do not log request or response bodies.

### Configuration

- All settings come from environment variables through `Settings` in `core/config.py`.
- No secrets or `.env` files in the repository or the image. `.env` and `*.db` are in `.gitignore` and `.dockerignore`.

### CORS

- Do not add CORS middleware: there is no browser client, and Swagger UI is same-origin.
- If a frontend appears later, allow its exact origins. Never `allow_origins=["*"]`.

### Docker and dependencies

- Slim base image, non-root user, no build tools in the final image.
- The SQLite file lives on a mounted volume, not in the image.
- Commit `poetry.lock` so every install uses the same versions. Build the image with `poetry install --only main`.
- Poetry is not present in the runtime image.

### Documentation endpoints

- `/docs` and `/openapi.json` stay enabled; the brief requires Swagger.

## Not handled in the app

These belong to a reverse proxy or gateway and are out of scope here: TLS, request body size limits, security response headers. Rate limiting is handled in the app (see "Rate limiting"); a gateway can add a second, global limit on top.
