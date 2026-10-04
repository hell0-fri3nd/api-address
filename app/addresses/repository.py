from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from .models import Address


def _active_addresses() -> Select[tuple[Address]]:
    return select(Address).where(Address.deleted_at.is_(None))


def create_address(db: Session, address: Address) -> Address:
    db.add(address)
    db.flush()
    return address


def get_address(db: Session, address_id: int) -> Address | None:
    return db.scalars(_active_addresses().where(Address.id == address_id)).first()


def list_addresses(db: Session, limit: int, offset: int) -> list[Address]:
    query = _active_addresses().order_by(Address.id).limit(limit).offset(offset)
    return list(db.scalars(query))


def list_addresses_in_latitude_band(
    db: Session, min_latitude: float, max_latitude: float
) -> list[Address]:
    query = _active_addresses().where(
        Address.latitude.between(min_latitude, max_latitude)
    )
    return list(db.scalars(query))
