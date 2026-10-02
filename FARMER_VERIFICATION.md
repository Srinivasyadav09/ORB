# ORB Farmer Profiles and Verification (Phase 4)

Phase 4 implements private customer/farmer profile APIs, a public farmer summary, and an admin-managed verification workflow. It reuses the Phase 3 `customers` and `farmers` fields; no new migration is required. Profile image fields accept URL references only. File upload is not implemented.

## Profile endpoints

All private routes require a Bearer access token and enforce the profile role from the authenticated database user. `email` is returned for the account owner but cannot be edited here; email changes require a future authentication/security flow.

- `GET /api/customers/me` and `PATCH /api/customers/me` require CUSTOMER.
- `GET /api/farmers/me`, `PATCH /api/farmers/me`, and `GET /api/farmers/me/verification` require FARMER.
- `GET /api/farmers/{farmer_id}` is public and returns only farmer/farm display fields plus `is_verified`. It does not expose email, phone, account status, verification dates, or credentials.

PATCH bodies accept only editable profile fields. Unknown fields, including role, account flags, verification states/timestamps, IDs, password data, and server timestamps, are rejected. Phone values are normalized and checked using the same international-number validation rules as registration. A duplicate phone returns 409. Full names, farm names, locations, descriptions, and image URL lengths follow explicit Pydantic limits. An empty PATCH is rejected.

## Verification states and transitions

New farmer registrations start at `SUBMITTED`. Status changes are restricted to the following transitions:

| Current state | Allowed next state(s) |
|---|---|
| SUBMITTED | VERIFYING, REJECTED |
| VERIFYING | COMPLETED, REJECTED |
| REJECTED | SUBMITTED |
| COMPLETED | none (terminal) |

Only ADMIN can list/retrieve review applications and change state. Farmers can read their own status but cannot change it through profile or verification requests. An attempt at a forbidden transition returns 409; a non-admin receives 403. The admin list supports `page` (minimum 1), `page_size` (1–100), and optional enum `status` filtering. Admin records include contact details for review but exclude passwords, JWTs, and internal account flags.

A REJECTED application can be resubmitted only by an administrator moving it to SUBMITTED after the farmer has corrected their information. This sets `verification_submitted_at` to the current timezone-aware UTC timestamp and clears `verification_completed_at`. Transitioning to COMPLETED sets `verification_completed_at`. Other non-completed states have no completion timestamp. Completion is terminal, so its timestamp is preserved. The client cannot supply timestamps.

The response includes a user-facing status message. Current response fields are:

```json
{
  "status": "VERIFYING",
  "submitted_at": "2026-09-23T12:00:00Z",
  "completed_at": null,
  "status_message": "Your farm details are being reviewed."
}
```

The current schema has no timestamp for when the application entered VERIFYING or REJECTED and no rejection-reason field. The API therefore reports current status and submission/completion dates, rather than inventing timeline dates or rejection details. Add audit/event fields through a later migration if the UI needs a dated stage-by-stage timeline.

## Admin update example

```http
PATCH /api/admin/farmers/7f63f5d9-32d9-4a22-a9de-d946d55b29b6/verification
Authorization: Bearer <admin-access-token>
Content-Type: application/json
```

```json
{"status":"VERIFYING"}
```

The response contains the farmer UUID, new status, submitted/completed timestamps, and the matching status message. Invalid enum values fail validation with 422; an existing but disallowed transition returns 409; an unknown farmer returns 404.

## OpenAPI

The API routes are grouped under `Customers`, `Farmers`, and `Admin / Farmer Verification` tags. Private operations declare the existing Bearer authentication dependency, which appears as BearerAuth in Swagger. The public farmer summary has no auth requirement.
