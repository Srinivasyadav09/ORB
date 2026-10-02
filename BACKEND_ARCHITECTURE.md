# ORB Backend Architecture Proposal

## Implementation status

Phase 2 implemented the API/runtime foundation. Phase 3 added User/Customer/Farmer models, authentication, bearer JWT role dependencies, and Alembic revision `20260923_0002`. Phase 4 added customer/farmer profiles, public farmer summaries, and admin verification review without schema changes. Phase 5 adds category/product models and marketplace APIs. Phase 6 adds customer-owned addresses. Phase 7 adds persistent customer carts and stock validation. Phase 8 adds transactional checkout, order/address/product snapshots, stock decrement, migration `20260924_0006`, and PostgreSQL integration tests. Real payment processing and later integration features remain future work.

## Goals and boundaries

ORB uses a modular monolith: one FastAPI deployment, one PostgreSQL database, one REST API and domain modules with explicit service/repository boundaries. The React/Vite client remains a separate application. This document describes the target architecture and current implementation status.

Use Python 3.12+, FastAPI, SQLAlchemy 2.x async APIs, PostgreSQL, Alembic, Pydantic v2, pydantic-settings, JWT, pytest/httpx and Docker/Compose. Password hashing should use Argon2 (or bcrypt if deployment constraints require it). Uploaded files begin on local development storage behind an upload-service interface.

## Proposed source tree

```text
backend/
  app/
    __init__.py
    main.py
    core/
      __init__.py
      config.py              # pydantic-settings; no committed secrets
      security.py            # hash/verify, JWT issue/verify, refresh rotation
      dependencies.py        # current-user and role dependencies
      logging.py             # redacted structured logging config
    db/
      __init__.py
      base.py                # DeclarativeBase and model metadata
      session.py             # async engine/session dependency
    models/
      __init__.py
      user.py
      customer.py
      farmer.py
      product.py
      category.py
      address.py
      cart.py
      cart_item.py
      order.py
      order_item.py
      rating.py
      notification.py
      image.py
      refresh_token.py       # or equivalent session/revocation entity
    schemas/
      __init__.py
      common.py              # error/pagination/common IDs
      auth.py
      user.py
      customer.py
      farmer.py
      product.py
      category.py
      address.py
      cart.py
      order.py
      rating.py
      notification.py
      image.py
    api/
      __init__.py
      deps.py
      routes/
        __init__.py
        auth.py
        customers.py
        farmers.py
        products.py
        categories.py
        addresses.py
        cart.py
        orders.py
        ratings.py
        notifications.py
        uploads.py
        health.py
    services/
      __init__.py
      auth_service.py
      customer_service.py
      farmer_service.py
      product_service.py
      category_service.py
      address_service.py
      cart_service.py
      order_service.py
      rating_service.py
      notification_service.py
      upload_service.py
      payment_service.py
    repositories/
      __init__.py
      user_repository.py
      customer_repository.py
      farmer_repository.py
      product_repository.py
      order_repository.py
      address_repository.py
      cart_repository.py
      rating_repository.py
      notification_repository.py
    utils/
      __init__.py
      pagination.py
      ids.py
      time.py
  alembic/
    env.py
    versions/
  tests/
    __init__.py
    conftest.py
    test_auth.py
    test_customers.py
    test_farmers.py
    test_products.py
    test_addresses.py
    test_cart.py
    test_orders.py
    test_ratings.py
    test_notifications.py
    test_uploads.py
  scripts/
    seed.py
  uploads/
    .gitkeep
  .env.example
  .gitignore
  alembic.ini
  requirements.txt
  Dockerfile
  docker-compose.yml
  README.md
```

The requested root folders (`app/`, `alembic/`, `tests/`, `scripts/`, `uploads/`) sit inside `backend/`. Routers should be grouped under `app/api/routes/`; schemas, models, services and repositories remain separate. Keep imports one-directional: routes → services → repositories/models; schemas are shared at API boundaries; core/db are infrastructure dependencies.

## Request lifecycle and layering

1. **ASGI composition (`main.py`)** creates the FastAPI app, loads settings, configures CORS/logging/exception handlers, mounts `/api` routers and health routes.
2. **API routes** declare tags, summaries, descriptions, request/response models, status codes and dependencies. They parse inputs, invoke one service operation, and return a schema. No business rule or SQL query belongs in a route.
3. **Dependencies** yield an async SQLAlchemy session and resolve current JWT user/role. Resource ownership is checked in service/repository logic as well as the role dependency.
4. **Pydantic schemas** separate create, patch and read DTOs; use field constraints and ORM/model validation where appropriate. Never return ORM internals, hashes or token secrets.
5. **Services** enforce domain rules, orchestrate repositories, transaction boundaries and notifications/payment/upload interfaces.
6. **Repositories** own SQLAlchemy query construction, filtering, pagination and persistence. They do not decide HTTP status codes.
7. **SQLAlchemy models** express UUID keys, FK relationships, indexes, uniqueness/check constraints and UTC timestamps.
8. **Database session** uses one async engine/sessionmaker per process and request-scoped sessions. Services explicitly commit or use transaction contexts for multi-row operations.

## PostgreSQL and SQLAlchemy model proposal

Use UUID primary keys and UTC `created_at`/`updated_at` values. Database constraints should protect uniqueness and invariants even when requests race.

- **User:** UUID, normalized unique email, password hash, role enum CUSTOMER/FARMER/ADMIN, active state and timestamps.
- **Customer:** one-to-one unique `user_id`; full name, phone, optional profile image and preferences.
- **Farmer:** one-to-one unique `user_id`; full name, phone, farm name/location/description, farm/profile image references, verification enum and submitted/completed/rejected audit fields.
- **Image:** UUID, uploader FK, generated key, URL, content type, size, created time. Product/farmer references should point to image metadata or stable object URL.
- **Category:** UUID, unique case-insensitive name, optional description/image URL, active flag and timestamps. Products reference categories by FK; inactive categories are hidden from public browsing.
- **Product:** UUID, farmer/category FKs, name/description, `NUMERIC(12,2)` price, controlled unit, `NUMERIC(12,3)` available quantity, one image URL/reference, DRAFT/ACTIVE/INACTIVE status and timestamps. ACTIVE plus quantity zero remains an active but unavailable listing; availability is computed separately.
- Product indexes cover owner, category, status, price, creation order, and PostgreSQL trigram search on name/description. `pg_trgm` also indexes category name search. These support actual inventory filters and case-insensitive substring search without loading rows into Python.
- **ProductImage (optional):** product/image FKs, sort order, primary flag, if multiple product images are approved.
- **Address:** UUID, customer FK, contact, label, address lines, city/state/postal/country, optional coordinates and default flag. Ensure one default per customer with a partial unique index where supported or transaction-safe update.
- **Cart:** UUID and unique customer FK. **CartItem:** UUID, cart/product FKs, quantity, timestamps, unique `(cart_id, product_id)`.
- **Order:** UUID plus optional human-readable order number, customer FK, address snapshot, order status, payment status/method, computed subtotal/fee/total and timestamps.
- **OrderItem:** UUID, order/product FKs and immutable product/farmer/name/unit/price snapshots plus quantity and line total.
- **Rating:** UUID, customer/order/order-item/product FKs, integer 1–5, optional bounded review, timestamps; unique customer/order item.
- **Notification:** UUID, user FK, title/message/type, read timestamp, created timestamp, optional related entity IDs.
- **RefreshToken/session:** UUID/user FK, only a hash/JTI representation, expiry, revoked/rotated timestamps. Never persist raw refresh token.

Relationships: User to optional Customer/Farmer profile (one-to-one); Farmer to Products (one-to-many); Category to Products; Customer to Addresses/Cart/Orders/Ratings; Cart to CartItems; Order to OrderItems; Product to OrderItems/Ratings; User to Notifications/sessions. Product/order history remains readable after a product is deactivated; order items retain snapshots.

## Domain services and transaction rules

- `AuthService`: customer/farmer registration, password hashing, duplicate checks, login, access/refresh issuing/rotation, logout/revocation and safe current-user projection.
- `CustomerService`: own-profile reads/patch validation.
- `FarmerService`: own profile, public farmer projection, verification reads, admin-only state transitions with audit metadata.
- `ProductService`/`CategoryService`: marketplace filters/pagination, category reads, owner-scoped product lifecycle transitions and inventory changes, Decimal validation, and completed-farmer publication gate.
- `UploadService`: content-based MIME/size validation, generated names, local storage adapter, file metadata persistence and future object-storage adapter. Do not couple product/farmer service to `pathlib` or a specific cloud vendor.
- `AddressService`: ownership-scoped CRUD, default replacement and snapshot source.
- `CartService`: per-customer cart CRUD, active product and quantity/stock validation; prices shown are informational only.
- `OrderService`: create order in one transaction; lock/recheck products, calculate price/fees/totals, snapshot address/items, reserve/decrement stock, clear cart, create order notifications. Use an idempotency mechanism and conditional update/row locks to avoid duplicate orders and overselling.
- `PaymentService`: interface for COD and development mock payment. Order service receives normalized payment outcome; no real payment secrets or card data in DB.
- `RatingService`: authorization, delivered/order-item/duplicate/range checks and aggregate updates or aggregate queries.
- `NotificationService`: create/list/read/read-all, user scoping and unread count.

## API route modules

Mount routers under `/api` with tags and explicit response models:

- `auth.py`: register customer/farmer, login, refresh, me, logout.
- `customers.py`: own profile get/patch.
- `farmers.py`: own profile get/patch, public farmer get, own verification read, own product and farmer-order routes as specified by the backend requirements.
- `products.py`: public listing/detail with database-side search, filters, sorting and pagination.
- `categories.py`: public active category list/detail.
- `farmer_products.py`: authenticated farmer inventory reads, creation, updates and soft deactivation.
- `admin_products.py`: admin product list/detail for moderation.
- `addresses.py`: customer-scoped CRUD/default.
- `cart.py`: customer cart and item CRUD.
- `orders.py`: customer checkout/list/detail.
- `ratings.py`: order rating submission and product rating reads.
- `notifications.py`: list/read/read-all.
- `uploads.py`: multipart image upload.
- `health.py`: process and database health.

Use standard HTTP codes (201 create, 204 delete where body is unnecessary, 401 unauthenticated, 403 forbidden, 404 absent/out-of-scope resource, 409 uniqueness/state conflict, 422 request validation). Centralize API exception serialization. Proposed error shape: FastAPI-compatible `{"detail": "..."}`; validation errors remain structured and must not expose stack traces.

## Authentication and security

- Bearer JWT access token with short configurable expiry; refresh token rotation/revocation stored hashed or represented by revocable session ID. Define whether refresh is secure HttpOnly cookie or response body before frontend wiring; cookie choice needs CSRF policy.
- Argon2id preferred password hashing. Normalize email and use DB uniqueness to prevent duplicate-registration races.
- `get_current_user` resolves active user, `require_role` gates CUSTOMER/FARMER/ADMIN routes, and service-level ownership checks guard each resource.
- Configure CORS from explicit environment origins; do not use wildcard origins with credentials.
- pydantic-settings reads DB/JWT/upload/CORS settings. `.env.example` contains placeholders only; `.env` is ignored.
- Redact passwords, authorization headers, JWTs, refresh tokens, payment details and unnecessary PII from logs. Add rate-limiting architecture only if deployment demonstrates need.
- Uploads use generated safe filenames, strict allowlisted image MIME/content checks and size limit, never execute files. Store outside application source.

## Migrations, testing and seed

- Alembic imports all model metadata and uses the configured async/sync migration strategy consistently. Create an initial revision; document `alembic upgrade head`, `alembic downgrade -1`, and revision creation.
- Pytest + httpx tests use isolated test DB/config and dependency overrides. Cover authentication/roles/ownership, validation, product status and stock, cart, transactional order creation/stock race behavior, rating rules, address defaults, notifications and upload validation.
- `scripts/seed_marketplace.py` runs only when explicitly invoked outside production. It seeds standard categories and sample products only for a farmer whose verification is COMPLETED. It never creates fake credentials or runs automatically.
- Run migrations against disposable test DB; test concurrent inventory updates where practical. API tests should not use production data.

## Docker/local runtime

- `Dockerfile` runs the ASGI app on port 8000 with a non-root production process and health check.
- Compose services: `backend` and `db` (PostgreSQL). Use environment references and a named DB volume; do not commit credentials. Local API at `http://localhost:8000`, Swagger `/docs`, OpenAPI `/openapi.json`.
- `DATABASE_URL` in the container uses the Compose DB service name; browser-facing frontend `VITE_API_BASE_URL` uses host `localhost:8000/api`.
- `GET /health` checks application liveness; `/health/db` performs a lightweight DB connectivity check and reports degraded status without leaking DSN details.

## Frontend integration boundary

The React app currently persists mock domain state locally and does not call the API service modules. Integration should happen through the existing context/custom-hook domain layer and `src/services/api`, not JSX. Each domain should expose loading/error/data state; screens should render loading, useful errors/retry and empty states while preserving current UI design. Normalize backend snake_case/UUID/pagination/status shapes in a single adapter layer. Handle stale local mock IDs/Data URLs deliberately, and update context only after successful mutations. Full endpoint/body/response mapping is in `FRONTEND_BACKEND_API_MAP.md`.

## Recommended build sequence

1. Agree on response envelope, request/response field names, token transport, order/verification states, and upload flow.
2. Skeleton/config/database/health/error/CORS/Docker/Alembic.
3. Auth/security and roles.
4. Customer/farmer profiles and admin verification.
5. Categories/products and farmer inventory.
6. Uploads and addresses.
7. Cart, payment abstraction and transactional orders.
8. Ratings and notifications.
9. Seed data, tests, docs, migration/runtime review.
10. Frontend integration by domain with loading/error/empty/mutation states.
