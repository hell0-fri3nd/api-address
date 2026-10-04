# 02 — Architecture

## Stack

| Concern | Choice |
|---------|--------|
| Language | Python 3.12+ |
| Web framework | FastAPI 0.142 |
| Validation | Pydantic 2.13, pydantic-settings 2.15 |
| ORM | SQLAlchemy 2.1 (typed `Mapped` / `mapped_column` style, sync) |
| Database | SQLite (file) |
| Distance | geopy 2.5 (`geodesic`) |
| Rate limiting | limits 5 (fixed window, in-memory storage) |
| Server | Uvicorn |
| Tests | pytest 9, FastAPI `TestClient` with `httpx2` |
| Lint / format | Ruff |
| Dependencies | Poetry 2.5 (`pyproject.toml` + `poetry.lock`) |
| Packaging | Docker + Docker Compose |

`TestClient` needs `httpx2`: current Starlette warns that plain `httpx` is deprecated for it.

## Style: modular monolith, layered inside each module

One deployable app. Code is grouped by **domain module** (`addresses/`), and each module is layered internally. Shared plumbing lives in `core/`.

```
app/
├── main.py              # FastAPI app, lifespan, routers, exception handlers
├── core/
│   ├── __init__.py      # re-exports Base, get_db, settings, UTCDateTime, utcnow
│   ├── config.py        # Settings (env vars)
│   ├── database.py      # engine, SessionLocal, Base, get_db, UTCDateTime, utcnow
│   ├── errors.py        # NotFoundError, RateLimitExceededError, RFC 9457 problem responses, exception handlers
│   └── rate_limit.py    # enforce_rate_limit dependency
└── addresses/
    ├── __init__.py      # exports router
    ├── api.py           # routes
    ├── services.py      # business logic
    ├── repository.py    # database queries
    ├── schemas.py       # Pydantic request / response models
    └── models.py        # SQLAlchemy model
tests/
├── conftest.py
└── addresses/           # one test file per endpoint
Dockerfile
docker-compose.yml
pyproject.toml           # dependencies, Ruff and pytest config
poetry.lock              # committed
```

A new domain is a new sibling folder of `addresses/` with the same files.

**Each module owns its models.** The `Address` model lives in `app/addresses/models.py`. There is no shared `app/models/` or `app/schemas/` folder, and `core/` holds no models, only `Base` and the shared column helpers.

A model registers its table on `Base.metadata` when its module is imported. `main.py` imports the `addresses` router, which imports the model, so `create_all` sees the table. Keep that import at the top of `main.py`.

## Dependencies (Poetry)

- Poetry manages dependencies only; the app is not built as a package (`package-mode = false`).
- Runtime dependencies go in `[project].dependencies`; test and lint tools go in the `dev` group.
- Use the Poetry 2 layout below. Do not use the legacy `[tool.poetry.dependencies]` tables.
- `poetry.lock` is committed. No `requirements.txt`.
- Ruff and pytest settings live in `pyproject.toml`; no separate config files.

```toml
[project]
name = "address-book-api"
version = "0.1.0"
requires-python = ">=3.12,<4.0"
dependencies = [
    "fastapi (>=0.142,<0.143)",
    "geopy (>=2.5,<3.0)",
    "limits (>=5,<6)",
    "pydantic (>=2.13,<3.0)",
    "pydantic-settings (>=2.15,<3.0)",
    "sqlalchemy (>=2.1,<2.2)",
    "uvicorn (>=0.54,<0.55)",
]

[dependency-groups]
dev = [
    "pytest (>=9.1,<10.0)",
    "httpx2 (>=2.13,<3.0)",
    "ruff (>=0.16,<0.17)",
]

[tool.poetry]
package-mode = false

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["poetry-core>=2.0.0,<3.0.0"]
build-backend = "poetry.core.masonry.api"
```

| Task | Command |
|------|---------|
| Install everything | `poetry install` |
| Add a runtime dependency | `poetry add <package>` |
| Add a dev dependency | `poetry add --group dev <package>` |
| Run the API | `poetry run uvicorn app.main:app --reload` |
| Run tests | `poetry run pytest -q` |

## Layers

Calls go one way: `api → services → repository → models`.

| Layer | Does | Must not |
|-------|------|----------|
| `api.py` | Parse HTTP input, call one service function, return the response schema and status code | Query the database, hold business rules |
| `services.py` | Business rules, soft delete, distance filtering, commit the transaction | Import FastAPI, raise `HTTPException` |
| `repository.py` | Build and run SQLAlchemy queries; always filter `deleted_at IS NULL` | Commit, hold business rules |
| `schemas.py` | Validate input, shape output | Touch the database |
| `models.py` | Table definition | Hold logic |

Services raise `NotFoundError`; one handler in `core/errors.py` turns it into a 404. All errors are RFC 9457 problem responses (see `03-design.md`).

## Decisions and trade-offs

| Decision | Why | Trade-off / when to revisit |
|----------|-----|-----------------------------|
| Sync SQLAlchemy, `def` endpoints | SQLite has no real async driver benefit; less code than `aiosqlite` + async sessions | Move to async when switching to PostgreSQL under high concurrency |
| Plain functions for services and repository, `db: Session` passed in | No classes or interfaces needed for one module | Introduce classes if a second repository implementation appears |
| No repository interface (ABC / Protocol) | One database, one implementation | Same as above |
| `Base.metadata.create_all` in the app lifespan | One table; no migration history to manage | Add Alembic at the first schema change after release |
| Distance search = SQL latitude band, then geopy `geodesic` in Python | No SQLite extension and no hand-written distance math | See "Scaling limits" |
| One Uvicorn worker | SQLite allows a single writer | Raise workers only after moving off SQLite |
| Rate limit as a router dependency using `limits` directly | slowapi 0.1.10 cannot see routes inside FastAPI 0.142's included routers, so its middleware silently limits nothing | Revisit slowapi when it supports the current FastAPI router layout |
| Rate limit counters in process memory | No extra service to run | Move to Redis storage before running more than one worker or instance |
| Two-stage Docker build | Poetry stays out of the runtime image | A few more Dockerfile lines than a single stage |

## Runtime

- `get_db` yields one `Session` per request and closes it.
- Engine uses `connect_args={"check_same_thread": False}` because FastAPI runs `def` endpoints in a thread pool.
- Routes are mounted under `/api/v1`.

## Configuration

| Env var | Default | Purpose |
|---------|---------|---------|
| `DATABASE_URL` | `sqlite:///./address_book.db` | SQLAlchemy URL |
| `LOG_LEVEL` | `INFO` | Log level |
| `RATE_LIMIT` | `60/minute` | Requests per client, per endpoint ([`limits` notation](https://limits.readthedocs.io/en/stable/quickstart.html#rate-limit-string-notation)) |

## Docker

Two stages, both on `python:3.12-slim` with workdir `/app` (the virtualenv is only portable if image and path match):

1. **builder**: `pip install poetry==2.5.1`, set `POETRY_VIRTUALENVS_IN_PROJECT=true`, copy `pyproject.toml` and `poetry.lock`, run `poetry install --only main --no-interaction`. This creates `/app/.venv` without dev tools.
2. **runtime**: copy `/app/.venv` from the builder, put `/app/.venv/bin` on `PATH`, copy `app/`, switch to a non-root user.

Copy the two Poetry files before `app/` so the dependency layer is cached between code changes.

- Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Compose mounts a named volume at `/data` and sets `DATABASE_URL=sqlite:////data/address_book.db`, so data survives container restarts.
- `.dockerignore` excludes `.git`, `.env`, `.venv`, `*.db`, `tests/`, caches.

## Scaling limits

- **SQLite**: single writer, single host. Switch to PostgreSQL when the API needs concurrent writes or more than one instance.
- **Distance search**: every row in the latitude band is loaded and measured in Python. `geodesic` costs about 80 µs per row (measured), so 10,000 candidates take about 0.8 s. The band has no longitude limit, so globally spread data reaches that sooner than local data. First step: switch to geopy's `great_circle` (about 4 µs per row, up to 0.5% less accurate). Beyond that: PostGIS (`ST_DWithin`) or SpatiaLite.
