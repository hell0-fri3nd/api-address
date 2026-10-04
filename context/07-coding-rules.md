# 07 — Coding Rules

## Golden rule

**The code explains itself.** Clear names and small functions replace comments.

- No comments that restate the code. No docstrings on obvious functions.
- A comment is allowed only for a *why* the code cannot show (example: why the distance query filters on latitude only).
- No commented-out code, no `TODO` left in the submission.

## Priorities, in order

1. **Simplicity**: the least code that fully meets `01-product-requirements.md`.
2. **Consistency**: match the patterns already in the codebase and in these context files.
3. **Scalability**: do not build for it now; the known limits are written in `02-architecture.md`.

## Keep it simple

- Follow the layer order in `02-architecture.md`: `api → services → repository → models`. No layer skips another or calls upward.
- No abstraction without a second use: no base repository, generic CRUD class, interface, factory, or decorator for a single case.
- Plain functions over classes for services and repository.
- Use the libraries in `02-architecture.md` instead of hand-written equivalents (distance is geopy, validation is Pydantic).
- No new dependency without a requirement that needs it. Add one with `poetry add`, never by editing `poetry.lock`.
- No feature outside `01-product-requirements.md`.

## Formatting

- Ruff formats and lints (`ruff format`, `ruff check`), configured in `pyproject.toml` with rule sets `E`, `F`, `I`, `N`.
- Line length 88 (Ruff's default). PEP 8 prefers 79 and allows up to 99 by team agreement.
- **More than 3 parameters or arguments: one per line, with a trailing comma.** Three or fewer stay on one line if they fit.

```python
def get_address(db: Session, address_id: int) -> Address: ...


def problem_response(
    request: Request,
    status: int,
    detail: str,
    errors: list[dict] | None = None,
) -> JSONResponse: ...
```

- Model columns always put one argument per line, as in `05-schema.md`.

## Naming

Three conventions, applied in this order: Python (PEP 8), then HTTP, then SQL. One concept keeps one name across all three: the column `postal_code` is the model attribute, the schema field, and the JSON field `postal_code`.

### 1. Python: PEP 8

FastAPI code follows [PEP 8](https://peps.python.org/pep-0008/). Ruff enforces it (rule set `N`, pep8-naming).

| Object | Rule | Example |
|--------|------|---------|
| Package, module | Short, lowercase `snake_case` | `addresses/`, `repository.py` |
| Function, variable, parameter | `snake_case` | `create_address`, `address_id` |
| Class (model, schema, exception) | `PascalCase` | `Address`, `AddressCreate` |
| Exception | `PascalCase` ending in `Error` | `NotFoundError` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| Type alias | `PascalCase` | `Latitude` |
| Module-private name | Leading underscore | `_active_addresses` |
| Test | `test_<action>_<condition>_returns_<status>` | `test_create_missing_city_returns_422` |

Project rules on top of PEP 8:

- Full words: `latitude`, `longitude`, `address_id`. Not `lat`, `lng`, `addr`.
- Functions are verb + noun: `create_address`, `soft_delete_address`, `find_nearby_addresses`. The same verb is used in every layer for the same operation.
- Schemas are `Address<Purpose>`: `AddressCreate`, `AddressUpdate`, `AddressRead`.
- Booleans start with `is_` or `has_`.
- Units go in the name: `distance_km`, `MIN_KM_PER_LATITUDE_DEGREE`.
- No magic numbers; name them as constants (`MAX_PAGE_SIZE`).

### 2. HTTP

| Object | Rule | Example |
|--------|------|---------|
| Path | Lowercase, plural noun, no verb, no trailing slash | `/api/v1/addresses` |
| Multi-word path segment | `kebab-case` | `/postal-codes` |
| Version | Prefix in the path | `/api/v1` |
| Path parameter | `snake_case`, `<resource>_id`, same as the Python parameter | `{address_id}` |
| Query parameter | `snake_case`, unit in the name | `distance_km`, `limit`, `offset` |
| JSON field | `snake_case`, same as the column name | `postal_code`, `created_at` |
| Non-CRUD read | Noun or adjective under the collection | `/addresses/nearby`, not `/getNearbyAddresses` |
| Header | Standard `Hyphenated-Pascal-Case`; no custom `X-` headers | `Location`, `Content-Type` |
| OpenAPI tag | Plural resource, capitalised | `Addresses` |

The HTTP method carries the verb; the path never does:

| Action | Method | Success |
|--------|--------|---------|
| Create | POST | 201 |
| Read | GET | 200 |
| Partial update | PATCH | 200 |
| Soft delete | DELETE | 204 |

Error status codes and bodies are in `03-design.md`.

### 3. SQL

| Object | Rule | Example |
|--------|------|---------|
| Table | Plural entity name, `snake_case` | `addresses` |
| Column | `snake_case`, singular, no table prefix | `postal_code` |
| Primary key | `id` | `id` |
| Foreign key column | `<entity>_id` | `contact_id` |
| Timestamp | `<verb>_at`, stored in UTC | `created_at`, `deleted_at` |
| Boolean | `is_<state>` | `is_primary` |
| Index | `ix_<table>_<columns>` | `ix_addresses_latitude` |
| Check constraint | `ck_<table>_<rule>` | `ck_addresses_latitude_range` |
| Unique constraint | `uq_<table>_<columns>` | `uq_contacts_email` |
| Foreign key constraint | `fk_<table>_<column>` | `fk_addresses_contact_id` |

- Every constraint and index has an explicit name; never rely on generated names.
- No SQL reserved words as names (`order`, `group`, `user`).
- The model class is the singular of the table name: `Address` → `addresses`.

`05-schema.md` applies these rules to the current schema.

## Typing

- Type hints on every function signature, including the return type.
- `X | None`, not `Optional[X]`. Built-in generics (`list[Address]`).
- FastAPI dependencies and parameters use `Annotated[...]`.

## File size and splitting

Start with one file per layer (`services.py`, `repository.py`, ...). Split only when a file holds about three or more separate concerns or becomes hard to scan. Then turn that file into a package with one file per concern and re-export from `__init__.py`, so imports elsewhere do not change:

```
addresses/
└── services/
    ├── __init__.py   # re-exports the public functions
    ├── create.py
    ├── update.py
    ├── delete.py
    └── search.py
```

Each domain module owns its own `models.py`, `schemas.py`, `services.py`, `repository.py`, and `api.py`. No top-level `models/` or `schemas/` folder.

Code that belongs to another domain goes in that domain's module, not in `addresses/`. Code shared by two or more domains goes in `core/`.

## FastAPI and SQLAlchemy

- Routes are thin: validate through the schema, call one service function, return.
- Services raise `NotFoundError`; they never import from `fastapi`.
- Only services call `db.commit()`. Repository functions never commit.
- SQLAlchemy 2.x style only: `select()`, `db.scalars()`, `Mapped[...]`. No legacy `db.query()`.
- Pydantic v2 style only: `model_config = ConfigDict(...)`, `model_dump()`, `model_validate()`. No `class Config`, `.dict()`, or `orm_mode`.

## Tests

- Every endpoint change comes with its cases from `04-test-plan.md`.
- One behaviour per test. No logic (loops, conditionals) inside tests; use `parametrize`.

## Before finishing a task

```bash
poetry run ruff format . && poetry run ruff check . && poetry run pytest -q
```
