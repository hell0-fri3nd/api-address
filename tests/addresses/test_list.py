import pytest

from tests.helpers import ADDRESSES_URL, address_url, assert_validation_problem


@pytest.fixture
def three_addresses(create_address) -> list[dict]:
    return [
        create_address(city="Manila"),
        create_address(city="Cebu"),
        create_address(city="Davao"),
    ]


def test_list_no_data_returns_200(client):
    response = client.get(ADDRESSES_URL)

    assert response.status_code == 200
    assert response.json() == []


def test_list_three_addresses_returns_200(client, three_addresses):
    response = client.get(ADDRESSES_URL)

    assert response.status_code == 200
    assert response.json() == three_addresses


def test_list_limit_and_offset_returns_200(client, three_addresses):
    response = client.get(ADDRESSES_URL, params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    assert response.json() == three_addresses[1:]


def test_list_soft_deleted_address_returns_200(client, three_addresses):
    client.delete(address_url(three_addresses[0]["id"]))

    response = client.get(ADDRESSES_URL)

    assert response.status_code == 200
    assert response.json() == three_addresses[1:]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"limit": "abc"},
        {"foo": 1},
    ],
)
def test_list_invalid_query_returns_422(client, params):
    response = client.get(ADDRESSES_URL, params=params)

    errors = assert_validation_problem(response)
    assert errors[0]["loc"][0] == "query"
