# ORB Customer Addresses (Phase 6)

Phase 6 adds customer-owned delivery addresses to the backend. Routes require a bearer access token and the `CUSTOMER` role. The customer profile is derived from the authenticated user; callers cannot submit a customer ID. Missing and foreign address IDs both return 404.

## Endpoints

| Method | Path | Behavior |
|---|---|---|
| `GET` | `/api/addresses` | List the authenticated customer's addresses, oldest first |
| `POST` | `/api/addresses` | Create an address (201) |
| `GET` | `/api/addresses/default` | Retrieve the default address (404 when none is selected) |
| `GET` | `/api/addresses/{address_id}` | Retrieve one owned address |
| `PATCH` | `/api/addresses/{address_id}` | Partially update an owned address; omitted fields remain unchanged |
| `PATCH` | `/api/addresses/{address_id}/default` | Select an owned address as default |
| `DELETE` | `/api/addresses/{address_id}` | Delete an owned address (204) |

## Rules

- Full name, phone, address line 1, city, state, postal code, and country are required. Phone normalization follows customer profile rules. Text is trimmed; extra and internal fields are rejected.
- Latitude and longitude are optional `NUMERIC(9,6)` values. They must be provided together, with latitude in `[-90, 90]` and longitude in `[-180, 180]`. The backend only stores client-supplied coordinates; it does not request or infer location.
- Each customer can have at most one default address. Mutations lock the customer row, and PostgreSQL has a partial unique index as a second safeguard.
- Deleting the default address promotes the oldest remaining address (UUID breaks timestamp ties). Deleting the final address leaves no default.
- Customer deletion cascades to its addresses, consistent with the existing customer profile/user deletion behavior.

## Migration and tests

Migration: `20260924_0004` (`20260924_0004_customer_addresses.py`). Integration coverage is in `backend/tests/test_addresses.py`. Run the Phase 6/full backend checks from `backend/` with the configured PostgreSQL URLs described in `backend/README.md`.

## Limitations

Coordinates are not geocoded or checked against the textual address. No pagination or address search is provided in this phase.
