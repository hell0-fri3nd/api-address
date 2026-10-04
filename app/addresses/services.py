from geopy.distance import geodesic
from sqlalchemy.orm import Session

from app.core import NotFoundError, utcnow

from . import repository
from .models import Address
from .schemas import (
    AddressCreate,
    AddressNearbyRead,
    AddressRead,
    AddressUpdate,
    ListParams,
    NearbyParams,
)

MIN_KM_PER_LATITUDE_DEGREE = 110.57
DISTANCE_DECIMALS = 3


def create_address(db: Session, address_data: AddressCreate) -> Address:
    address = repository.create_address(db, Address(**address_data.model_dump()))
    db.commit()
    return address


def list_addresses(db: Session, params: ListParams) -> list[Address]:
    return repository.list_addresses(db, params.limit, params.offset)


def get_address(db: Session, address_id: int) -> Address:
    address = repository.get_address(db, address_id)

    if address is None:
        raise NotFoundError("Address not found")

    return address


def update_address(
    db: Session, address_id: int, address_data: AddressUpdate
) -> Address:
    address = get_address(db, address_id)

    for field, value in address_data.model_dump(exclude_unset=True).items():
        setattr(address, field, value)

    db.commit()
    return address


def soft_delete_address(db: Session, address_id: int) -> None:
    address = get_address(db, address_id)
    address.deleted_at = utcnow()
    db.commit()


def find_nearby_addresses(db: Session, params: NearbyParams) -> list[AddressNearbyRead]:
    # Filtering on latitude only keeps the band correct across the poles and the
    # ±180° meridian; geodesic below measures the real distance.
    latitude_delta = params.distance_km / MIN_KM_PER_LATITUDE_DEGREE
    candidates = repository.list_addresses_in_latitude_band(
        db, params.latitude - latitude_delta, params.latitude + latitude_delta
    )

    origin = (params.latitude, params.longitude)
    nearby = []

    for address in candidates:
        distance_km = geodesic(origin, (address.latitude, address.longitude)).km

        if distance_km <= params.distance_km:
            nearby.append(
                AddressNearbyRead(
                    **AddressRead.model_validate(address).model_dump(),
                    distance_km=round(distance_km, DISTANCE_DECIMALS),
                )
            )

    nearby.sort(key=lambda address: address.distance_km)
    return nearby[: params.limit]
