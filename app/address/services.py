from sqlalchemy.orm import Session

from .models import Address
from .repository import AddressRepository
from .schemas import AddressCreate


class AddressService:
    def __init__(self, db: Session):
        self.repository = AddressRepository(db)

    def create_address(self, address_data: AddressCreate) -> Address:
        address = Address(
            street=address_data.street,
            city=address_data.city,
            state=address_data.state,
            postal_code=address_data.postal_code,
            country=address_data.country,
            latitude=address_data.latitude,
            longitude=address_data.longitude,
        )

        return self.repository.create(address)
