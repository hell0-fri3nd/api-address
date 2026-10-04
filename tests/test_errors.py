import pytest
from fastapi.testclient import TestClient

from app.core import get_db
from app.main import app
from tests.helpers import (
    ADDRESSES_URL,
    address_url,
    assert_problem,
    assert_validation_problem,
)


def test_error_unknown_address_returns_404(client):
    response = client.get(address_url(999))

    problem = assert_problem(response, 404, "Address not found")
    assert "errors" not in problem


@pytest.mark.parametrize(
    "method, url, kwargs, location",
    [
        ("post", ADDRESSES_URL, {"json": {}}, "body"),
        ("get", ADDRESSES_URL, {"params": {"limit": 0}}, "query"),
        ("get", address_url("abc"), {}, "path"),
    ],
)
def test_error_validation_failure_returns_422(client, method, url, kwargs, location):
    response = client.request(method, url, **kwargs)

    errors = assert_validation_problem(response)
    assert errors[0]["loc"][0] == location


def test_error_unknown_route_returns_404(client):
    response = client.get("/api/v1/nope")

    assert_problem(response, 404, "Not Found")


def test_error_wrong_method_returns_405(client):
    response = client.put(address_url(1))

    assert_problem(response, 405, "Method Not Allowed")


def test_error_unhandled_exception_returns_500():
    def broken_get_db():
        raise RuntimeError("secret database path /var/data.db")

    app.dependency_overrides[get_db] = broken_get_db

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(ADDRESSES_URL)

    app.dependency_overrides.clear()
    problem = assert_problem(response, 500, "Internal server error")
    assert "secret" not in response.text
    assert "errors" not in problem


def test_error_openapi_documents_problem_schemas_returns_200(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schemas = response.json()["components"]["schemas"]
    assert "ProblemDetail" in schemas
    assert "ValidationProblemDetail" in schemas
    assert "HTTPValidationError" not in schemas
