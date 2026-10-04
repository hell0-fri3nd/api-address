from tests.helpers import address_url, assert_problem, assert_validation_problem


def test_get_existing_id_returns_200(client, create_address):
    address = create_address()

    response = client.get(address_url(address["id"]))

    assert response.status_code == 200
    assert response.json() == address
    assert response.json()["created_at"].endswith("Z")
    assert response.json()["updated_at"].endswith("Z")


def test_get_unknown_id_returns_404(client):
    response = client.get(address_url(999))

    assert_problem(response, 404, "Address not found")


def test_get_soft_deleted_id_returns_404(client, create_address):
    address = create_address()
    client.delete(address_url(address["id"]))

    response = client.get(address_url(address["id"]))

    assert_problem(response, 404, "Address not found")


def test_get_non_integer_id_returns_422(client):
    response = client.get(address_url("abc"))

    errors = assert_validation_problem(response)
    assert errors[0]["loc"] == ["path", "address_id"]
