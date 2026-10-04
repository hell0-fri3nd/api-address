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
