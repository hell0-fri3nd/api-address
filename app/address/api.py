from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import get_db
from .schemas import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
)
from .services import AddressService


api = APIRouter(prefix="/addresses", tags=["Addresses"])


@api.post("",response_model=AddressResponse,status_code=status.HTTP_201_CREATED)
def create_address(
    address_data: AddressCreate,
    db: Session = Depends(get_db),
):
    service = AddressService(db)
    return service.create_address(address_data)


# @api.get(
#     "/{address_id}",
#     response_model=AddressResponse,
# )
# def get_address(
#     address_id: int,
#     db: Session = Depends(get_db),
# ):
#     service = AddressService(db)

#     address = service.get_address(address_id)

#     if address is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Address not found",
#         )

#     return address


# @api.put(
#     "/{address_id}",
#     response_model=AddressResponse,
# )
# def update_address(
#     address_id: int,
#     address_data: AddressUpdate,
#     db: Session = Depends(get_db),
# ):
#     service = AddressService(db)

#     address = service.update_address(
#         address_id,
#         address_data,
#     )

#     if address is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Address not found",
#         )

#     return address


# @api.delete(
#     "/{address_id}",
#     status_code=status.HTTP_204_NO_CONTENT,
# )
# def delete_address(
#     address_id: int,
#     db: Session = Depends(get_db),
# ):
#     service = AddressService(db)

#     deleted = service.delete_address(address_id)

#     if not deleted:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Address not found",
#         )

#     return None
