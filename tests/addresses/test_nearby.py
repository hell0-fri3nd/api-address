import pytest

from tests.helpers import NEARBY_URL, address_url, assert_validation_problem

MANILA = {"latitude": 14.5995, "longitude": 120.9842}
CEBU = {"latitude": 10.3157, "longitude": 123.8854}
ORIGIN = {"latitude": 0, "longitude": 0}
ONE_DEGREE_NORTH = {"latitude": 1, "longitude": 0}
VALID_PARAMS = ORIGIN | {"distance_km": 10}


def nearby_ids(response) -> list[int]:
    return [address["id"] for address in response.json()]


@pytest.fixture
def origin_and_north(create_address) -> tuple[dict, dict]:
    return create_address(**ORIGIN), create_address(**ONE_DEGREE_NORTH)


def test_nearby_within_110_km_returns_200(client, origin_and_north):
    origin, _ = origin_and_north

    response = client.get(NEARBY_URL, params=ORIGIN | {"distance_km": 110})

    assert response.status_code == 200
    assert nearby_ids(response) == [origin["id"]]


def test_nearby_within_111_km_returns_200(client, origin_and_north):
    origin, north = origin_and_north

    response = client.get(NEARBY_URL, params=ORIGIN | {"distance_km": 111})

    assert response.status_code == 200
    assert nearby_ids(response) == [origin["id"], north["id"]]
    distances = [address["distance_km"] for address in response.json()]
    assert distances == pytest.approx([0.0, 110.574], abs=0.001)


@pytest.mark.parametrize(
    "distance_km, is_included",
    [(569, False), (570, True)],
)
def test_nearby_manila_to_cebu_returns_200(
    client, create_address, distance_km, is_included
):
    create_address(**MANILA)
    cebu = create_address(**CEBU)

    response = client.get(NEARBY_URL, params=MANILA | {"distance_km": distance_km})

    assert response.status_code == 200
    assert (cebu["id"] in nearby_ids(response)) is is_included


def test_nearby_no_address_in_range_returns_200(client, create_address):
    create_address(**MANILA)

    response = client.get(NEARBY_URL, params=VALID_PARAMS)

    assert response.status_code == 200
    assert response.json() == []


def test_nearby_soft_deleted_address_returns_200(client, create_address):
    address = create_address(**ORIGIN)
    client.delete(address_url(address["id"]))

    response = client.get(NEARBY_URL, params=VALID_PARAMS)

    assert response.status_code == 200
    assert response.json() == []


def test_nearby_limit_returns_200(client, origin_and_north):
    origin, _ = origin_and_north

    response = client.get(NEARBY_URL, params=ORIGIN | {"distance_km": 111, "limit": 1})

    assert response.status_code == 200
    assert nearby_ids(response) == [origin["id"]]


@pytest.mark.parametrize(
    "address_location, search_location, distance_km",
    [
        ((0, -179.9), (0, 179.9), 25),
        ((89.9, 100), (89.9, -80), 25),
        ((60, 30), (60, 0), 1660),
    ],
    ids=["across_meridian", "across_pole", "same_latitude_far_longitude"],
)
def test_nearby_edge_location_included_returns_200(
    client, create_address, address_location, search_location, distance_km
):
    address = create_address(
        latitude=address_location[0],
        longitude=address_location[1],
    )

    response = client.get(
        NEARBY_URL,
        params={
            "latitude": search_location[0],
            "longitude": search_location[1],
            "distance_km": distance_km,
        },
    )

    assert response.status_code == 200
    assert nearby_ids(response) == [address["id"]]


def test_nearby_same_latitude_just_out_of_range_returns_200(client, create_address):
    create_address(latitude=60, longitude=30)

    response = client.get(
        NEARBY_URL,
        params={"latitude": 60, "longitude": 0, "distance_km": 1659},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "params",
    [
        {"longitude": 0, "distance_km": 10},
        {"latitude": 0, "distance_km": 10},
        {"latitude": 0, "longitude": 0},
        VALID_PARAMS | {"latitude": 91},
        VALID_PARAMS | {"latitude": -91},
        VALID_PARAMS | {"longitude": 181},
        VALID_PARAMS | {"longitude": -181},
        VALID_PARAMS | {"distance_km": 0},
        VALID_PARAMS | {"distance_km": -1},
        VALID_PARAMS | {"distance_km": 20001},
        VALID_PARAMS | {"distance_km": "abc"},
        VALID_PARAMS | {"latitude": "nan"},
        VALID_PARAMS | {"distance_km": "inf"},
        VALID_PARAMS | {"limit": 0},
        VALID_PARAMS | {"limit": 101},
        VALID_PARAMS | {"foo": 1},
    ],
)
def test_nearby_invalid_query_returns_422(client, params):
    response = client.get(NEARBY_URL, params=params)

    errors = assert_validation_problem(response)
    assert errors[0]["loc"][0] == "query"


def test_nearby_route_is_not_parsed_as_id_returns_200(client):
    response = client.get(NEARBY_URL, params=VALID_PARAMS)

    assert response.status_code == 200
