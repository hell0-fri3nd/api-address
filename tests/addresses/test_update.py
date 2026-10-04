import pytest

from tests.helpers import (
    NEARBY_URL,
    address_url,
    assert_problem,
    assert_validation_problem,
)

NEW_VALUES = {
    "street": "1 Osmena Boulevard",
    "city": "Cebu City",
    "state": "Cebu",
    "postal_code": "6000",
    "country": "PH",
    "latitude": 10.3157,
    "longitude": 123.8854,
}


def test_update_one_field_returns_200(client, create_address):
    address = create_address()

    response = client.patch(address_url(address["id"]), json={"city": "Quezon City"})

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Quezon City"
    assert (
        body | {"city": address["city"], "updated_at": address["updated_at"]} == address
    )


def test_update_all_fields_returns_200(client, create_address):
    address = create_address()

    response = client.patch(address_url(address["id"]), json=NEW_VALUES)

    assert response.status_code == 200
    assert response.json() | NEW_VALUES == response.json()


def test_update_timestamps_returns_200(client, create_address):
    address = create_address()

    response = client.patch(address_url(address["id"]), json={"city": "Quezon City"})

    assert response.status_code == 200
    assert response.json()["updated_at"] > address["updated_at"]
    assert response.json()["created_at"] == address["created_at"]


@pytest.mark.parametrize("field", ["state", "postal_code"])
def test_update_clear_optional_field_returns_200(client, create_address, field):
    address = create_address(state="Metro Manila")

    response = client.patch(address_url(address["id"]), json={field: None})

    assert response.status_code == 200
    assert response.json()[field] is None


def test_update_coordinates_returns_200(client, create_address):
    address = create_address()
    new_location = {"latitude": 10.3157, "longitude": 123.8854}

    response = client.patch(address_url(address["id"]), json=new_location)

    assert response.status_code == 200
    nearby = client.get(NEARBY_URL, params=new_location | {"distance_km": 1})
    assert [found["id"] for found in nearby.json()] == [address["id"]]


def test_update_empty_body_returns_422(client, create_address):
    address = create_address()

    response = client.patch(address_url(address["id"]), json={})

    assert_validation_problem(response)


@pytest.mark.parametrize(
    "field, value",
    [
        ("street", None),
        ("city", None),
        ("country", None),
        ("latitude", None),
        ("longitude", None),
        ("street", "   "),
        ("city", "a" * 101),
        ("postal_code", "a" * 21),
        ("latitude", 90.0001),
        ("longitude", -180.0001),
        ("latitude", "abc"),
        ("foo", 1),
        ("id", 1),
        ("deleted_at", "2026-01-01T00:00:00Z"),
    ],
)
def test_update_invalid_value_returns_422(client, create_address, field, value):
    address = create_address()

    response = client.patch(address_url(address["id"]), json={field: value})

    assert_validation_problem(response)


def test_update_failed_validation_leaves_address_unchanged_returns_200(
    client, create_address
):
    address = create_address()
    client.patch(address_url(address["id"]), json={"city": "", "latitude": 100})

    response = client.get(address_url(address["id"]))

    assert response.status_code == 200
    assert response.json() == address


def test_update_unknown_id_returns_404(client):
    response = client.patch(address_url(999), json={"city": "Quezon City"})

    assert_problem(response, 404, "Address not found")


def test_update_soft_deleted_id_returns_404(client, create_address):
    address = create_address()
    client.delete(address_url(address["id"]))

    response = client.patch(address_url(address["id"]), json={"city": "Quezon City"})

    assert_problem(response, 404, "Address not found")


def test_update_non_integer_id_returns_422(client):
    response = client.patch(address_url("abc"), json={"city": "Quezon City"})

    errors = assert_validation_problem(response)
    assert errors[0]["loc"] == ["path", "address_id"]
