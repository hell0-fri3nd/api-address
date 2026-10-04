# 05 — Database Schema

SQLite, one table. `Address` is the only entity.

## Naming rules

Same SQL rules as `07-coding-rules.md`.

| Object | Rule | Example |
|--------|------|---------|
| Table | Plural entity name, `snake_case` | `addresses` |
| Model class | Singular entity name, `PascalCase` | `Address` |
| Column | `snake_case`, singular, no table prefix | `postal_code` |
| Primary key | `id` | `id` |
| Foreign key (future) | `<entity>_id` | `contact_id` |
| Timestamp | `<verb>_at`, stored in UTC | `created_at` |
| Boolean (future) | `is_<state>` | `is_primary` |
| Index | `ix_<table>_<columns>` | `ix_addresses_latitude` |
| Check constraint | `ck_<table>_<rule>` | `ck_addresses_latitude_range` |
| Unique constraint (future) | `uq_<table>_<columns>` | `uq_contacts_email` |
| Foreign key constraint (future) | `fk_<table>_<column>` | `fk_addresses_contact_id` |

## Table `addresses`

| Column | Type | Null | Notes |
|--------|------|------|-------|
| `id` | INTEGER | no | Primary key, autoincrement |
| `street` | VARCHAR(255) | no | |
| `city` | VARCHAR(100) | no | |
| `state` | VARCHAR(100) | yes | |
| `postal_code` | VARCHAR(20) | yes | |
| `country` | VARCHAR(100) | no | |
| `latitude` | FLOAT | no | Decimal degrees, −90 to 90 |
| `longitude` | FLOAT | no | Decimal degrees, −180 to 180 |
| `created_at` | DATETIME | no | Set on insert |
| `updated_at` | DATETIME | no | Set on insert and on every update |
| `deleted_at` | DATETIME | yes | `NULL` = active; a timestamp = soft deleted |

Constraints and indexes:

- `ck_addresses_latitude_range`: `latitude BETWEEN -90 AND 90`
- `ck_addresses_longitude_range`: `longitude BETWEEN -180 AND 180`
- `ix_addresses_latitude` on (`latitude`), used by the latitude-band query of the distance search

## Model (`app/addresses/models.py`)

```python
from datetime import datetime

from sqlalchemy import CheckConstraint, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core import Base, UTCDateTime, utcnow


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        CheckConstraint(
            "latitude BETWEEN -90 AND 90",
            name="ck_addresses_latitude_range",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180",
            name="ck_addresses_longitude_range",
        ),
        Index(
            "ix_addresses_latitude",
            "latitude",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    street: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    postal_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        UTCDateTime,
        nullable=True,
    )
```

## Timestamp helpers (`app/core/database.py`)

```python
class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=UTC) if value is not None else None


def utcnow() -> datetime:
    return datetime.now(UTC)
```

- `datetime.utcnow` is deprecated since Python 3.12; use `utcnow()` above.
- SQLite drops the timezone on write. `UTCDateTime` puts UTC back on read, so every response serializes timestamps with `Z`. Without it, the create response has `Z` and later reads do not.

## Rules

- The model lives inside its domain module: `app/addresses/models.py`. `core/` holds no models; it provides `Base`, `UTCDateTime`, and `utcnow`.
- Every read query filters `deleted_at IS NULL`. This lives in `repository.py` only.
- Never issue `DELETE FROM addresses`.
- SQLite does not enforce `VARCHAR` lengths. Length limits are enforced by the Pydantic schemas in `03-design.md` and must match the lengths here.
- Tables are created with `Base.metadata.create_all` at startup. No migrations yet (see `02-architecture.md`).
