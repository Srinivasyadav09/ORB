# ORB Authentication Design (Phase 3)

## Scope

This phase provides account authentication and role foundations only. It creates `users`, `customers`, and `farmers`; it does not implement products, orders, uploads, or other marketplace APIs. Farmer image upload is deferred; registration may store an existing `farm_image_url` when supplied.

## Roles and profiles

- `CUSTOMER`, `FARMER`, and `ADMIN` are PostgreSQL-backed `UserRole` values.
- Customer and farmer accounts are created with a one-to-one profile in the same database transaction.
- Farmer applications start at verification status `SUBMITTED`, with a submission timestamp. Registration ignores any client-supplied role or verification status.
- `is_verified` is separate from farmer verification status. Phase 3 has no email-verification flow, so self-registered accounts have `is_verified=false`.
- `require_customer`, `require_farmer`, and `require_admin` validate the active database user and role. JWT role claims are informational; authorization always uses the user row.

## Password policy and storage

Passwords must be at least 8 characters, no more than 128 characters, and not blank/whitespace-only. The minimum matches the current frontend form. Passwords are hashed with Argon2 using `pwdlib` in a worker thread so hashing does not block the async event loop; unknown/inactive-account login also performs a dummy hash verification to reduce timing differences. Plaintext passwords and hashes are never included in API responses or application request logs. Validation errors omit submitted input values to avoid echoing credentials or personal data.

## JWT design

The configured `JWT_SECRET_KEY` and `JWT_ALGORITHM` sign JWTs. Production rejects the development placeholder and requires a key of at least 32 characters. Access token claims include `sub` (UUID), `role`, `type=access`, `iat`, `exp`, and a unique `jti`. Refresh tokens contain `sub`, `type=refresh`, `iat`, `exp`, and `jti`; they avoid profile/email/phone data. Access lifetime is configured by `ACCESS_TOKEN_EXPIRE_MINUTES`; refresh lifetime by `REFRESH_TOKEN_EXPIRE_DAYS`.

Protected endpoints require `Authorization: Bearer <access_token>`. Signature, expiry, token type, current user existence, and active status are checked. A refresh token cannot be used as an access token. Invalid credentials and inactive accounts return generic HTTP 401 responses.

## Refresh and logout limitation

Refresh tokens are stateless in Phase 3: `POST /api/auth/refresh` validates the submitted refresh token and returns a new access token while preserving that refresh token until expiry. Rotation and revocation are not implemented because no persisted token-session model exists yet. `POST /api/auth/logout` confirms client-side token removal; it does not invalidate already issued tokens. Add a refresh-session table containing a hashed token/JTI, expiry, and revoked/rotated timestamps before claiming server-side logout or token revocation.

## Endpoints

### Customer registration

```http
POST /api/auth/register/customer
Content-Type: application/json
```

```json
{
  "email": "customer@example.com",
  "phone": "+919876543210",
  "password": "FreshPass123",
  "full_name": "Example Customer"
}
```

Returns `201` with safe user fields and `customer_profile`. Email is trimmed and lowercased; phone formatting spaces/dashes/parentheses are normalized. Duplicate email/phone returns `409`.

### Farmer registration

```http
POST /api/auth/register/farmer
Content-Type: application/json
```

```json
{
  "email": "farmer@example.com",
  "phone": "+919876543211",
  "password": "FreshPass123",
  "full_name": "Example Farmer",
  "farm_name": "Green Acres",
  "farm_location": "Hyderabad",
  "farm_description": "A local produce farm",
  "farm_image_url": "https://example.com/farm.jpg"
}
```

`farm_name`, description, and image URL are optional. The profile is created in `SUBMITTED` state. No image upload is performed by this endpoint.

### Login

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{"email":"customer@example.com","password":"FreshPass123"}
```

Returns `access_token`, `refresh_token`, `token_type`, `expires_in` (seconds), and safe `user`. Incorrect email/password and inactive accounts return the same generic `401` message.

### Refresh

```http
POST /api/auth/refresh
Content-Type: application/json
```

```json
{"refresh_token":"<refresh-jwt>"}
```

Returns a new access token, the same refresh token, expiry seconds, and the safe current user. Invalid, expired, wrong-type, missing-user, or inactive-user refresh credentials return `401`.

### Current user

```http
GET /api/auth/me
Authorization: Bearer <access-token>
```

Returns safe user fields and the caller's customer or farmer profile when present. It never returns `password_hash`.

### Logout

```http
POST /api/auth/logout
Authorization: Bearer <access-token>
```

Returns `200` with an instruction to remove client-stored tokens. It is not server-side revocation.

## Admin creation

There is no admin registration endpoint. Apply migrations, then run from `backend/`:

```bash
ADMIN_EMAIL=admin@example.com ADMIN_FULL_NAME="ORB Admin" python scripts/create_admin.py
```

The script prompts for an 8+ character password, hashes it, and creates an ADMIN user. It does not create an account automatically at startup. Do not put admin passwords in shell history or environment variables.

## Environment configuration

Configure `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `ENVIRONMENT`, and `CORS_ORIGINS` in the ignored `backend/.env`. Use a strong randomly generated secret outside local development. CORS remains restricted to the configured allowlist.

Apply migrations with `alembic upgrade head` before starting the API. Auth integration tests require `TEST_DATABASE_URL` to point to a dedicated disposable test database.
