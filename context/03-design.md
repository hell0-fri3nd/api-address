# 03 — API Design

## Conventions

- Base path `/api/v1`. Resource names are plural nouns; no verbs in paths.
- JSON in, JSON out, `snake_case` field names.
- Timestamps are UTC, ISO 8601 with a `Z` suffix.
- Distances are kilometres.
- Every route declares `response_model`, `status_code`, `summary`, and its error responses so Swagger is complete.
- Errors follow RFC 9457 (see "Errors").

## Endpoints

| Method | Path | Purpose | Success | Errors |
|--------|------|---------|---------|--------|
| POST | `/addresses` | Create | 201 + `Location` header | 422, 429 |
| GET | `/addresses` | List (paginated) | 200 | 422, 429 |
| GET | `/addresses/nearby` | Addresses within a distance | 200 | 422, 429 |
| GET | `/addresses/{address_id}` | Get one | 200 | 404, 422, 429 |
| PATCH | `/addresses/{address_id}` | Partial update | 200 | 404, 422, 429 |
| DELETE | `/addresses/{address_id}` | Soft delete | 204, no body | 404, 422, 429 |

Declare `/addresses/nearby` **before** `/addresses/{address_id}` in `api.py`, or `nearby` is parsed as an id and returns 422.

Update is PATCH only. PUT is left out on purpose: one update path is enough for the brief.

## Schemas (`schemas.py`)

| Schema | Use |
|--------|-----|
| `AddressCreate` | POST body |
| `AddressUpdate` | PATCH body, every field optional |
| `AddressRead` | Response |
| `AddressNearbyRead` | `AddressRead` + `distance_km` |
| `NearbyParams` | Query params of `/nearby` |
| `ListParams` | Query params of the list |

Input schemas use `ConfigDict(extra="forbid", str_strip_whitespace=True)`. `AddressRead` uses `from_attributes=True`.

Query parameter schemas are bound with `Annotated[NearbyParams, Query()]`.

### Address fields

| Field | Type | Create | Rules |
|-------|------|--------|-------|
| `street` | string | required | 1–255 chars after trim |
| `city` | string | required | 1–100 chars after trim |
| `state` | string or null | optional | 1–100 chars after trim |
| `postal_code` | string or null | optional | 1–20 chars after trim; no format check (formats differ per country) |
| `country` | string | required | 1–100 chars after trim |
| `latitude` | float | required | −90 to 90 |
| `longitude` | float | required | −180 to 180 |

`AddressRead` returns these plus `id`, `created_at`, `updated_at`. It never returns `deleted_at`.

### PATCH rules

- Only fields present in the body change (`model_dump(exclude_unset=True)`).
- Empty body `{}` → 422.
- `null` is accepted only for `state` and `postal_code` (clears the value). `null` for any other field → 422.

### Query parameters

| Endpoint | Param | Type | Rules |
|----------|-------|------|-------|
| List, Nearby | `limit` | int | 1–100, default 20 |
| List | `offset` | int | ≥ 0, default 0 |
| Nearby | `latitude` | float | required, −90 to 90 |
| Nearby | `longitude` | float | required, −180 to 180 |
| Nearby | `distance_km` | float | required, > 0 and ≤ 20000 |

Unknown query parameters → 422.

## Responses

- List returns a JSON array ordered by `id` ascending. No envelope with `total`: it would cost an extra count query nobody needs yet. Add `{items, total}` when a client needs page counts; that is a breaking change, so do it under `/api/v2`.
- Nearby returns a JSON array of `AddressNearbyRead`, ordered by `distance_km` ascending (rounded to 3 decimals), cut to `limit`.

Example `AddressRead`:

```json
{
  "id": 1,
  "street": "1 Rizal Park",
  "city": "Manila",
  "state": null,
  "postal_code": "1000",
  "country": "Philippines",
  "latitude": 14.5995,
  "longitude": 120.9842,
  "created_at": "2026-10-03T11:32:05.482058Z",
  "updated_at": "2026-10-03T11:32:05.482058Z"
}
```

## Errors (RFC 9457)

Every error response is an RFC 9457 problem details object, sent with `Content-Type: application/problem+json`.

| Member | Value |
|--------|-------|
| `type` | Always `"about:blank"` |
| `title` | HTTP status phrase, from `HTTPStatus(status).phrase` |
| `status` | HTTP status code |
| `detail` | Explanation of this occurrence |
| `instance` | Request path |
| `errors` | 422 only (extension member): one item per Pydantic error, with `loc`, `msg`, `type` |

| Status | When | `detail` |
|--------|------|----------|
| 404 | Id does not exist or is soft deleted | `Address not found` |
| 422 | Pydantic validation failed (body, path, or query) | `Request validation failed` |
| 404 / 405 | Unknown route or method | Starlette's message |
| 429 | Rate limit exceeded (see `06-security.md`) | `Rate limit exceeded: 60 per 1 minute`; `Retry-After` header in seconds |
| 500 | Unhandled error | `Internal server error`; traceback goes to the log only |

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Address not found",
  "instance": "/api/v1/addresses/9"
}
```

```json
{
  "type": "about:blank",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "Request validation failed",
  "instance": "/api/v1/addresses",
  "errors": [
    {
      "loc": ["body", "latitude"],
      "msg": "Input should be less than or equal to 90",
      "type": "less_than_equal"
    }
  ]
}
```

### Implementation (`core/errors.py`)

FastAPI has no built-in RFC 9457 support, so `core/errors.py` holds all of it:

- Models `ProblemDetail` and `ValidationProblemDetail` (adds `errors: list[ValidationErrorItem]`).
- One helper, `problem_response(request, status, detail, errors=None)`, builds every error response.
- Five exception handlers, registered in `main.py`:

| Exception | Status |
|-----------|--------|
| `RequestValidationError` | 422 |
| `NotFoundError` | 404 |
| `RateLimitExceededError` | 429 |
| Starlette `HTTPException` | Its own status (unknown route, wrong method) |
| `Exception` | 500 |

Rules:

- Validation is done by Pydantic only. Do not hand-write validation in routes or services.
- Each `errors` item copies only `loc`, `msg`, `type` from `exc.errors()`, never `input` or `ctx`. Echoing `input` breaks on a JSON body containing `NaN`: serialization fails and the client gets a 500 instead of a 422.
- Document the errors in Swagger: `responses={422: {"model": ValidationProblemDetail}, 429: {"model": ProblemDetail}}` on the router, and `responses={404: {"model": ProblemDetail}}` on the three `{address_id}` routes. This also replaces FastAPI's default `HTTPValidationError` schema.

Trade-offs:

- `about:blank` for every problem: no problem-type URIs to host or document. Add specific `type` URIs when clients need to branch on error kinds.
- `errors` items use Pydantic's `loc` rather than the JSON `pointer` shown in the RFC example, because a JSON pointer cannot address query and path parameters.
- Swagger lists the error media type as `application/json`, although the real responses are `application/problem+json`. Fixing the label needs hand-written OpenAPI content per response; not worth the code here.

## Soft delete

- DELETE sets `deleted_at = utcnow()`. The row is never removed.
- A soft-deleted address behaves as non-existent: GET, PATCH, and a second DELETE return 404; list and nearby skip it.

## Distance search

Distance is the WGS-84 geodesic distance from geopy. Do not hand-write a distance formula.

```python
from geopy.distance import geodesic

distance_km = geodesic((latitude, longitude), (address.latitude, address.longitude)).km
```

Steps:

1. The service computes a latitude band: `latitude_delta = distance_km / MIN_KM_PER_LATITUDE_DEGREE`.
2. The repository selects non-deleted rows with `latitude BETWEEN latitude - latitude_delta AND latitude + latitude_delta`.
3. The service measures each candidate with `geodesic`, keeps those with distance ≤ `distance_km`, sorts ascending, rounds to 3 decimals, applies `limit`.

Rules:

- `MIN_KM_PER_LATITUDE_DEGREE = 110.57`. One degree of latitude is never shorter than this, so the band cannot exclude an address that is in range.
- The SQL filter uses latitude only, no longitude. That keeps it correct near the poles and across the ±180° meridian without special cases; geopy handles both in step 3.
- geopy points are `(latitude, longitude)` tuples, in that order.
- Only validated coordinates reach geopy; it raises `ValueError` for a latitude outside ±90.
