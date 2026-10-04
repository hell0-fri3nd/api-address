from app.addresses.models import Address
from tests.helpers import (
    ADDRESSES_URL,
    NEARBY_URL,
    address_url,
    assert_problem,
    assert_validation_problem,
)


def test_delete_existing_id_returns_204(client, create_address):
    address = create_address()

    response = client.delete(address_url(address["id"]))

    assert response.status_code == 204
    assert response.content == b""


def test_delete_then_get_returns_404(client, create_address):
    address = create_address()
    client.delete(address_url(address["id"]))

    response = client.get(address_url(address["id"]))

    assert_problem(response, 404, "Address not found")


def test_delete_then_list_returns_200(client, create_address):
    address = create_address()
    client.delete(address_url(address["id"]))

    response = client.get(ADDRESSES_URL)

    assert response.status_code == 200
    assert response.json() == []


def test_delete_then_nearby_returns_200(client, create_address):
    address = create_address()
    client.delete(address_url(address["id"]))

    response = client.get(
        NEARBY_URL,
        params={
            "latitude": address["latitude"],
            "longitude": address["longitude"],
            "distance_km": 1,
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_delete_keeps_row_with_deleted_at_returns_204(
    client, create_address, db_session
):
    address = create_address()

    response = client.delete(address_url(address["id"]))

    assert response.status_code == 204
    row = db_session.get(Address, address["id"])
    assert row is not None
    assert row.deleted_at is not None


def test_delete_twice_returns_404(client, create_address):
    address = create_address()
    client.delete(address_url(address["id"]))

    response = client.delete(address_url(address["id"]))

    assert_problem(response, 404, "Address not found")


def test_delete_unknown_id_returns_404(client):
    response = client.delete(address_url(999))

    assert_problem(response, 404, "Address not found")


def test_delete_non_integer_id_returns_422(client):
    response = client.delete(address_url("abc"))

    errors = assert_validation_problem(response)
    assert errors[0]["loc"] == ["path", "address_id"]
