import pytest

from tests.helpers import ADDRESSES_URL, address_url, assert_validation_problem

REQUIRED_FIELDS = ["street", "city", "country", "latitude", "longitude"]


def test_create_valid_payload_returns_201(client, address_payload):
    response = client.post(ADDRESSES_URL, json=address_payload)

    assert response.status_code == 201
    body = response.json()
    assert body | address_payload == body
    assert {"id", "created_at", "updated_at"} <= body.keys()
    assert "deleted_at" not in body
    assert response.headers["location"] == address_url(body["id"])


def test_create_only_required_fields_returns_201(client, address_payload):
    del address_payload["state"]
    del address_payload["postal_code"]

    response = client.post(ADDRESSES_URL, json=address_payload)

    assert response.status_code == 201
    assert response.json()["state"] is None
    assert response.json()["postal_code"] is None


def test_create_strings_with_surrounding_spaces_returns_201(client, address_payload):
    address_payload["street"] = "  1 Rizal Park  "
    address_payload["city"] = " Manila "

    response = client.post(ADDRESSES_URL, json=address_payload)

    assert response.status_code == 201
    assert response.json()["street"] == "1 Rizal Park"
    assert response.json()["city"] == "Manila"


@pytest.mark.parametrize(
    "field, value",
    [
        ("latitude", 90),
        ("latitude", -90),
        ("longitude", 180),
        ("longitude", -180),
        ("street", "a" * 255),
    ],
)
def test_create_boundary_value_returns_201(client, address_payload, field, value):
    response = client.post(ADDRESSES_URL, json=address_payload | {field: value})

    assert response.status_code == 201
    assert response.json()[field] == value


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_create_missing_required_field_returns_422(client, address_payload, field):
    del address_payload[field]

    response = client.post(ADDRESSES_URL, json=address_payload)

    errors = assert_validation_problem(response)
    assert errors[0]["loc"] == ["body", field]


@pytest.mark.parametrize(
    "field, value",
    [
        ("street", ""),
        ("street", "   "),
        ("city", ""),
        ("city", "   "),
        ("country", ""),
        ("country", "   "),
        ("street", "a" * 256),
        ("city", "a" * 101),
        ("state", "a" * 101),
        ("postal_code", "a" * 21),
        ("country", "a" * 101),
        ("latitude", 90.0001),
        ("latitude", -90.0001),
        ("longitude", 180.0001),
        ("longitude", -180.0001),
        ("latitude", "abc"),
        ("longitude", "abc"),
        ("latitude", None),
        ("longitude", None),
        ("foo", 1),
        ("id", 1),
        ("created_at", "2026-01-01T00:00:00Z"),
        ("deleted_at", "2026-01-01T00:00:00Z"),
    ],
)
def test_create_invalid_value_returns_422(client, address_payload, field, value):
    response = client.post(ADDRESSES_URL, json=address_payload | {field: value})

    errors = assert_validation_problem(response)
    assert errors[0]["loc"] == ["body", field]


def test_create_nan_latitude_returns_422(client):
    body = (
        '{"street": "1 Rizal Park", "city": "Manila", "country": "Philippines", '
        '"latitude": NaN, "longitude": 120.9842}'
    )

    response = client.post(
        ADDRESSES_URL,
        content=body,
        headers={"Content-Type": "application/json"},
    )

    errors = assert_validation_problem(response)
    assert errors[0]["loc"] == ["body", "latitude"]


@pytest.mark.parametrize("body", ["{}", "[]", "{bad json", ""])
def test_create_invalid_body_returns_422(client, body):
    response = client.post(
        ADDRESSES_URL,
        content=body,
        headers={"Content-Type": "application/json"},
    )

    assert_validation_problem(response)


def test_create_validation_error_items_have_only_loc_msg_type_returns_422(
    client, address_payload
):
    response = client.post(ADDRESSES_URL, json=address_payload | {"latitude": 100})

    errors = assert_validation_problem(response)
    assert errors == [
        {
            "loc": ["body", "latitude"],
            "msg": "Input should be less than or equal to 90",
            "type": "less_than_equal",
        }
    ]
