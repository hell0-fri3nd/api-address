# 04 — Test Plan

## Setup

- pytest + FastAPI `TestClient` (`httpx2`). Tests call the API over HTTP; they do not call services directly.
- Database: in-memory SQLite (`sqlite://`, `StaticPool`, `check_same_thread=False`), injected by overriding `get_db`.
- A function-scoped fixture creates all tables before each test and drops them after, so tests never share data.
- Fixtures in `tests/conftest.py`: `client`, `db_session`, `address_payload` (valid body), `create_address` (factory that POSTs and returns the JSON).
- One file per endpoint: `test_create.py`, `test_list.py`, `test_get.py`, `test_update.py`, `test_delete.py`, `test_nearby.py`.
- Test names: `test_<action>_<condition>_returns_<status>`.
- Use `pytest.mark.parametrize` for the validation tables below; one row is one case.
- Each test asserts the status code first, then the body.
- Error responses are RFC 9457 problems. A shared helper `assert_problem(response, status, detail)` checks the content type and the five standard members (see "Errors").

Valid payload used below:

```json
{
  "street": "1 Rizal Park",
  "city": "Manila",
  "state": null,
  "postal_code": "1000",
  "country": "Philippines",
  "latitude": 14.5995,
  "longitude": 120.9842
}
```

## POST `/api/v1/addresses`

| Case | Expect |
|------|--------|
| Valid payload | 201; body matches input; has `id`, `created_at`, `updated_at`; no `deleted_at`; `Location` header is `/api/v1/addresses/{id}` |
| Only required fields (`state`, `postal_code` omitted) | 201; both are `null` |
| Strings with surrounding spaces | 201; values are trimmed |
| Boundary coordinates: `latitude` 90 and −90, `longitude` 180 and −180 | 201 |
| `street` of 255 chars | 201 |
| Missing each required field: `street`, `city`, `country`, `latitude`, `longitude` | 422; `errors[].loc` names the field |
| Empty or whitespace-only `street`, `city`, `country` | 422 |
| Too long: `street` 256, `city` 101, `state` 101, `postal_code` 21, `country` 101 | 422 |
| `latitude` 90.0001, −90.0001 | 422 |
| `longitude` 180.0001, −180.0001 | 422 |
| `latitude` or `longitude` is `"abc"` or `null` | 422 |
| `latitude` is `NaN` (raw JSON body) | 422, not 500 |
| Unknown field (`"foo": 1`) | 422 |
| Server-managed field sent (`id`, `created_at`, `deleted_at`) | 422 |
| Empty body `{}`; array body `[]`; malformed JSON | 422 |
| Any 422 | Problem body; each `errors` item has exactly `loc`, `msg`, `type` (no `input`) |

## GET `/api/v1/addresses`

| Case | Expect |
|------|--------|
| No data | 200; `[]` |
| Three addresses | 200; three items ordered by `id` |
| `limit=2&offset=1` | 200; second and third items |
| Soft-deleted address | Not in the list |
| `limit=0`, `limit=101`, `offset=-1`, `limit=abc` | 422 |
| Unknown query parameter | 422 |

## GET `/api/v1/addresses/{address_id}`

| Case | Expect |
|------|--------|
| Existing id | 200; body equals the created address; timestamps end with `Z` |
| Unknown id | 404; problem with `detail` `Address not found` |
| Soft-deleted id | 404 |
| `address_id` is `abc` | 422 |

## PATCH `/api/v1/addresses/{address_id}`

| Case | Expect |
|------|--------|
| One field (`city`) | 200; `city` changed; other fields unchanged |
| All fields | 200; all changed |
| `updated_at` after update | Later than before; `created_at` unchanged |
| `state: null`, `postal_code: null` | 200; value cleared |
| Coordinates only | 200; address is then found by a nearby search at the new location |
| Empty body `{}` | 422 |
| `null` for `street`, `city`, `country`, `latitude`, `longitude` | 422 |
| Same invalid values as POST (range, length, blank, type, unknown field, server-managed field) | 422 |
| Failed validation | Address is unchanged on the next GET |
| Unknown id | 404 |
| Soft-deleted id | 404 |
| `address_id` is `abc` | 422 |

## DELETE `/api/v1/addresses/{address_id}`

| Case | Expect |
|------|--------|
| Existing id | 204; empty body |
| After delete | GET 404; absent from list and nearby |
| After delete, checked through `db_session` | Row still exists; `deleted_at` is set |
| Second delete of the same id | 404 |
| Unknown id | 404 |
| `address_id` is `abc` | 422 |

## GET `/api/v1/addresses/nearby`

Reference distances (geopy `geodesic`):

| From | To | Distance |
|------|----|----------|
| (0, 0) | (1, 0) | 110.574 km |
| Manila (14.5995, 120.9842) | Cebu (10.3157, 123.8854) | 569.218 km |
| (0, 179.9) | (0, −179.9) | 22.264 km |
| (89.9, −80) | (89.9, 100) | 22.339 km |
| (60, 0) | (60, 30) | 1659.597 km |

| Case | Expect |
|------|--------|
| Addresses at (0, 0) and (1, 0); search (0, 0), `distance_km=110` | 200; only (0, 0) |
| Same data, `distance_km=111` | 200; both, nearest first; `distance_km` values 0.0 and 110.574 |
| Manila and Cebu; search Manila, 569 then 570 | Cebu excluded, then included |
| No address in range | 200; `[]` |
| Soft-deleted address in range | Excluded |
| `limit=1` with two in range | 200; nearest only |
| Across the ±180° meridian: address (0, −179.9), search (0, 179.9), 25 km | Included |
| Across a pole: address (89.9, 100), search (89.9, −80), 25 km | Included |
| Same latitude, far longitude: address (60, 30), search (60, 0), 1659 then 1660 | Excluded, then included |
| Missing `latitude`, `longitude`, or `distance_km` | 422 |
| `latitude` 91 / −91, `longitude` 181 / −181 | 422 |
| `distance_km` 0, −1, 20001, `abc` | 422 |
| `latitude=nan`, `distance_km=inf` | 422 |
| `limit=0`, `limit=101` | 422 |
| Unknown query parameter | 422 |
| Route order check: `/addresses/nearby` with valid params | 200 (not parsed as an id) |

Compare `distance_km` values with `pytest.approx(abs=0.001)`.

## Rate limiting

An autouse fixture resets the rate limit counters before each test.

| Case | Expect |
|------|--------|
| One request | 200 |
| One request over `RATE_LIMIT` on the same endpoint | 429 problem; `detail` `Rate limit exceeded: <limit>`; `Retry-After` between 1 and the window length |
| Another endpoint after one endpoint hits the limit | 200 (counters are per endpoint) |

## Errors (RFC 9457)

`assert_problem` checks:

- `Content-Type` is `application/problem+json`
- `type` is `about:blank`
- `status` equals the HTTP status code
- `title` equals `HTTPStatus(status).phrase` (compare to the phrase, not a literal: the 422 phrase differs between Python versions)
- `detail` equals the expected text
- `instance` equals the request path

| Case | Expect |
|------|--------|
| 404 for an unknown address | Problem; `detail` `Address not found`; no `errors` member |
| 422 from body, query, and path validation | Problem; `detail` `Request validation failed`; `errors[0].loc[0]` is `body`, `query`, `path` respectively |
| Unknown route (`/api/v1/nope`) | 404 problem |
| Wrong method (`PUT /api/v1/addresses/1`) | 405 problem |
| Unhandled exception in a route (force one with a dependency override; `TestClient(raise_server_exceptions=False)`) | 500 problem; `detail` `Internal server error`; no traceback or exception text in the body |
| OpenAPI schema (`/openapi.json`) | Contains `ProblemDetail` and `ValidationProblemDetail`; does not contain `HTTPValidationError` |

## Run

```bash
poetry run pytest -q
```
