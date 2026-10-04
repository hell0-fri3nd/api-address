from http import HTTPStatus

from httpx2 import Response

ADDRESSES_URL = "/api/v1/addresses"
NEARBY_URL = f"{ADDRESSES_URL}/nearby"


def address_url(address_id: int | str) -> str:
    return f"{ADDRESSES_URL}/{address_id}"


def assert_problem(response: Response, status: int, detail: str) -> dict:
    assert response.status_code == status
    assert response.headers["content-type"] == "application/problem+json"
    problem = response.json()
    assert problem["type"] == "about:blank"
    assert problem["status"] == status
    assert problem["title"] == HTTPStatus(status).phrase
    assert problem["detail"] == detail
    assert problem["instance"] == response.request.url.path
    return problem


def assert_validation_problem(response: Response) -> list[dict]:
    problem = assert_problem(response, 422, "Request validation failed")
    return problem["errors"]
