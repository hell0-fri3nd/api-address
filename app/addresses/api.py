from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.core import (
    ProblemDetail,
    ValidationProblemDetail,
    enforce_rate_limit,
    get_db,
)

from . import services
from .models import Address
from .schemas import (
    AddressCreate,
    AddressNearbyRead,
    AddressRead,
    AddressUpdate,
    ListParams,
    NearbyParams,
)

DbSession = Annotated[Session, Depends(get_db)]

NOT_FOUND_RESPONSE = {404: {"model": ProblemDetail}}

router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"],
    dependencies=[Depends(enforce_rate_limit)],
    responses={
        422: {"model": ValidationProblemDetail},
        429: {"model": ProblemDetail},
    },
)


@router.post(
    "",
    response_model=AddressRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an address",
)
def create_address(
    address_data: AddressCreate,
    request: Request,
    response: Response,
    db: DbSession,
) -> Address:
    address = services.create_address(db, address_data)
    response.headers["Location"] = request.url_for(
        "get_address", address_id=address.id
    ).path
    return address


@router.get(
    "",
    response_model=list[AddressRead],
    status_code=status.HTTP_200_OK,
    summary="List addresses",
)
def list_addresses(
    params: Annotated[ListParams, Query()], db: DbSession
) -> list[Address]:
    return services.list_addresses(db, params)


@router.get(
    "/nearby",
    response_model=list[AddressNearbyRead],
    status_code=status.HTTP_200_OK,
    summary="Find addresses within a distance of a location",
)
def find_nearby_addresses(
    params: Annotated[NearbyParams, Query()], db: DbSession
) -> list[AddressNearbyRead]:
    return services.find_nearby_addresses(db, params)


@router.get(
    "/{address_id}",
    response_model=AddressRead,
    status_code=status.HTTP_200_OK,
    summary="Get an address",
    responses=NOT_FOUND_RESPONSE,
)
def get_address(address_id: int, db: DbSession) -> Address:
    return services.get_address(db, address_id)


@router.patch(
    "/{address_id}",
    response_model=AddressRead,
    status_code=status.HTTP_200_OK,
    summary="Update an address",
    responses=NOT_FOUND_RESPONSE,
)
def update_address(
    address_id: int, address_data: AddressUpdate, db: DbSession
) -> Address:
    return services.update_address(db, address_id, address_data)


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete an address",
    responses=NOT_FOUND_RESPONSE,
)
def soft_delete_address(address_id: int, db: DbSession) -> None:
    services.soft_delete_address(db, address_id)
