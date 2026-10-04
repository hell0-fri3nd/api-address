# Address Book API

A REST API where users create, update, and soft delete addresses with coordinates, and retrieve the addresses within a given distance of a location. Backend only; FastAPI's Swagger UI (`/docs`) is the interface.

This is a technical exam submission. Reviewers judge correctness, clean structure, validation, and tests. Build exactly what is asked, as simply as possible.

## Context files

The files in `docs/` are the source of truth. Read the matching file before you start a task. If code and a context file disagree, follow the context file; if two context files disagree, stop and ask.

| Before you... | Read |
|---------------|------|
| Decide what is in or out of scope | `docs/01-product-requirements.md` |
| Create files, add a dependency, or touch Docker | `docs/02-architecture.md` |
| Add or change an endpoint, validation, errors, or the distance search | `docs/03-design.md` |
| Write or change tests | `docs/04-test-plan.md` |
| Touch the model or a query | `docs/05-schema.md` |
| Handle input, errors, logging, or configuration | `docs/06-security.md` |
| Write any code | `docs/07-coding-rules.md` |

## Stack

Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.1 (sync), SQLite, geopy, limits, Poetry, pytest, Ruff, Docker.

## Commands

```bash
poetry install                                # install all dependencies
poetry run uvicorn app.main:app --reload      # run; Swagger at http://localhost:8000/docs
poetry run pytest -q                          # tests
poetry run ruff format . && poetry run ruff check .
docker compose up --build                     # run in Docker
```

## Structure

```
app/
├── main.py          # app, lifespan, routers, exception handlers
├── core/            # config, database (Base, get_db), errors
└── addresses/       # api, services, repository, schemas, models
tests/
└── addresses/       # one test file per endpoint
```

A new domain is a new sibling of `addresses/` with the same files.

## Rules that always apply

- **Scope**: build only what `docs/01-product-requirements.md` lists. No authentication, GUI, or geocoding.
- **Simplicity first**: then consistency with existing code, then scalability. No abstraction without a second use. Plain functions for services and repository.
- **Layers**: `api → services → repository → models`. Routes are thin. Services never import `fastapi`. Only services commit.
- **Modules own their files**: models live in `app/addresses/models.py`. No top-level `models/` or `schemas/` folder.
- **Validation**: Pydantic schemas only. Input schemas use `extra="forbid"`.
- **Errors**: every error is an RFC 9457 problem (`application/problem+json`), built in `core/errors.py`.
- **Rate limiting**: every endpoint is rate limited per client (`enforce_rate_limit` on the router, `RATE_LIMIT` env var); over the limit is a 429 problem. Non-negotiable.
- **Soft delete**: never delete rows. Every query filters `deleted_at IS NULL`, in `repository.py`.
- **Distance**: geopy `geodesic`. Never hand-write a distance formula.
- **Comments**: the code explains itself. Comment only a *why* the code cannot show.
- **Formatting**: more than 3 parameters or arguments go one per line.
- **Naming**: PEP 8 for Python, then the HTTP and SQL rules in `docs/07-coding-rules.md`.
- **Dependencies**: add with `poetry add`. Use the stack's libraries instead of hand-written equivalents.

## Build order

`core/` → model → schemas → repository → services → api → tests → Docker.

## Done means

- `poetry run ruff format .`, `poetry run ruff check .`, and `poetry run pytest -q` all pass.
- Every endpoint change has its cases from `docs/04-test-plan.md`.
- No `TODO`, commented-out code, or feature outside the requirements.
