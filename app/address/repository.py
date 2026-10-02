from .models import Address

class AddressRepository:
    def __init__(self, session):
        self.session = session

    def get_address_by_id(self, address_id: int):
        return self.session.query(Address).filter(Address.id == address_id).first()

    def create_address(self, address_data: dict):
        new_address = Address(**address_data)
        self.session.add(new_address)
        self.session.commit()
        return new_address