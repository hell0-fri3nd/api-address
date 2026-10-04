import pytest

from app.core.rate_limit import RATE_LIMIT
from tests.helpers import ADDRESSES_URL, NEARBY_URL, assert_problem


@pytest.fixture
def exhausted_list_limit(client) -> None:
    for _ in range(RATE_LIMIT.amount):
        assert client.get(ADDRESSES_URL).status_code == 200


def test_rate_limit_within_limit_returns_200(client):
    response = client.get(ADDRESSES_URL)

    assert response.status_code == 200


def test_rate_limit_exceeded_returns_429(client, exhausted_list_limit):
    response = client.get(ADDRESSES_URL)

    assert_problem(response, 429, f"Rate limit exceeded: {RATE_LIMIT}")
    assert 1 <= int(response.headers["retry-after"]) <= RATE_LIMIT.get_expiry()


def test_rate_limit_is_counted_per_endpoint_returns_200(client, exhausted_list_limit):
    response = client.get(
        NEARBY_URL, params={"latitude": 0, "longitude": 0, "distance_km": 1}
    )

    assert response.status_code == 200
