# 01 — Product Requirements

## What we are building

An **Address Book REST API**: a backend-only service where API users store addresses with coordinates and find the addresses within a given distance of a location.

This is a **technical exam submission** for a backend developer role. Reviewers judge correctness, clean structure, validation, and tests. Keep everything small and readable; do not add features that are not listed here.

There is no GUI. FastAPI's built-in Swagger UI (`/docs`) is the user interface.

## Original brief

> Create an address book application where API users can create, update and delete (soft delete) address.
>
> The Address should:
> - contain the coordinates of the address
> - be saved to an SQLite database
> - be validated
>
> API Users should also be able to retrieve the addresses that are within a given distance and location coordinates.
>
> Important: The application does not need a GUI. (Built-in FastAPI's Swagger doc is sufficient)

## Functional requirements

| ID | Requirement | Source |
|----|-------------|--------|
| FR-1 | Create an address | Brief |
| FR-2 | Update an address | Brief |
| FR-3 | Soft delete an address: the row stays in the database and disappears from every API response | Brief |
| FR-4 | Every address has coordinates (`latitude`, `longitude`) | Brief |
| FR-5 | All input is validated; invalid input is rejected with a clear error | Brief |
| FR-6 | Data is persisted in SQLite | Brief |
| FR-7 | Retrieve addresses within a given distance (km) of given coordinates | Brief |
| FR-8 | Get one address by id, and list addresses | Added: needed to verify FR-1 to FR-3 from Swagger |
| FR-9 | All endpoints are documented and usable from `/docs` | Brief |
| FR-10 | Every endpoint is rate limited per client; over the limit returns 429 | Added: non-negotiable project requirement |

## Out of scope

Do not build these:

- GUI or frontend
- Authentication, users, or per-user address books
- Geocoding (the client supplies the coordinates)
- Hard delete, restore of deleted addresses
- Duplicate detection (two identical addresses are allowed)

## Done means

- All FR items work from Swagger UI.
- Every case in `04-test-plan.md` passes.
- `docker compose up` starts the API with a persistent SQLite file.
- The code follows `07-coding-rules.md`.

## Related context files

| File | Content |
|------|---------|
| `02-architecture.md` | Stack, project structure, layers |
| `03-design.md` | Endpoints, validation, errors, distance search |
| `04-test-plan.md` | Test cases per endpoint |
| `05-schema.md` | Database schema and naming |
| `06-security.md` | Security rules |
| `07-coding-rules.md` | Code style rules |
