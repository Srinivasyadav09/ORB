# ORB — Online Raithu Bazaar API

Phase 8 provides authentication, profiles, marketplace categories/products, saved customer addresses, persistent carts, and transactional customer checkout with order history and immutable delivery/product snapshots. Real payments, fulfillment management, and React integration remain future work.

## Requirements

- Python 3.12+
- PostgreSQL 16 for local development (or Docker Compose)
- Docker Engine and Docker Compose for containerized development

## Project structure

```text
backend/
  app/main.py
  app/core/       # settings, logging, security, auth dependencies
  app/db/         # async SQLAlchemy base/session
  app/models/     # User, Customer, Farmer, Address, Category, Product
  app/schemas/    # auth, profile, verification, product, category, and address DTOs
  app/repositories/ # user, customer, farmer, product, category, and address queries
  app/services/   # auth, profiles, verification, marketplace, and address rules
  app/api/routes/ # health, auth, profiles, marketplace, addresses, farmer products, admin
  tests/          # health, auth, profiles, verification, products, and addresses
  scripts/        # admin creation and explicit marketplace seed
  uploads/        # reserved development mount; uploads not implemented
  alembic/        # async migration environment and schema revisions
```

## Virtual environment and dependencies

From the repository root:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

The checked-in environment example contains development-only PostgreSQL credentials and a placeholder JWT secret. Never use those values outside local development. `.env` is ignored by Git.

Compose exposes PostgreSQL on host port `5433` (container port `5432`) to avoid colliding with an existing local PostgreSQL service. For local Uvicorn outside Docker, set `DATABASE_URL` to your host database, for example `postgresql+asyncpg://orb_user:orb_password@localhost:5433/orb_db` when using the Compose database.

## Run PostgreSQL locally

Create a local PostgreSQL database and role matching your private `.env`, or use Compose below. Do not put production credentials in this repository.

## Run FastAPI locally

With PostgreSQL running and `DATABASE_URL` set in `backend/.env`:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The process health route does not require a database. `/api/health/db` executes `SELECT 1` and returns HTTP 503 when the configured DB is unreachable.

## Run with Docker Compose

From repository root, ensure `backend/.env` exists (copy `backend/.env.example` first), then run:

```bash
docker compose up --build
```

Compose starts PostgreSQL and waits for its `pg_isready` health check before starting the API. Inside Compose, the sample `DATABASE_URL` uses hostname `db`. Stop services with `docker compose down`; keep the named volume to retain local DB contents. `docker compose down -v` deletes that development database volume.

## Alembic migrations

Run commands from `backend/` with the environment configured:

```bash
alembic upgrade head
alembic current
alembic revision --autogenerate -m "describe change"
alembic downgrade -1
```

The initial baseline is empty. Revision `20260923_0002` creates users/customers/farmers. Phase 5 adds categories/products and marketplace indexes in revision `20260923_0003`; Phase 6 adds customer addresses and coordinate/default-address constraints in revision `20260924_0004`. SQLAlchemy models inherit from `app.db.base.Base`; `alembic/env.py` imports model metadata for autogeneration.

## Tests

```bash
cd backend
pytest
```

Set `TEST_DATABASE_URL` to a dedicated disposable PostgreSQL database before running the full suite, for example `TEST_DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5433/orb_test pytest`. The integration fixture creates missing schema objects (including `pg_trgm`) and uses unique test users; never point it at production or a database containing valuable data. The suite fails clearly if `TEST_DATABASE_URL` is missing instead of silently skipping tests.

## API documentation

With the app running:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- Root health: http://localhost:8000/health
- API health: http://localhost:8000/api/health
- Database health: http://localhost:8000/api/health/db

## Authentication (Phase 3)

See [`AUTHENTICATION.md`](../AUTHENTICATION.md) for API examples, JWT claims, role dependencies, password policy, refresh/logout limitations, and admin setup. See [`FARMER_VERIFICATION.md`](../FARMER_VERIFICATION.md) for verification rules and [`PRODUCTS.md`](../PRODUCTS.md) for the Phase 5 catalog, lifecycle and API behavior. Customer and farmer registration return safe user/profile objects (not tokens); login and refresh return bearer tokens. Run migrations before using the routes. Admin accounts are created explicitly with `python scripts/create_admin.py` after setting `ADMIN_EMAIL` and `ADMIN_FULL_NAME`; the script prompts for the password.

The refresh token is currently stateless and not rotated or revocable. Logout is client-side token removal only. A later session/revocation table is required before making logout invalidate tokens or rotating/revoking sessions.


## Marketplace seed data (development only)

After migrations, run `python -m scripts.seed_marketplace` explicitly from `backend/`. It creates the seven sample categories and adds seven fake active products only when a completed farmer exists. If no completed farmer is available, it leaves the categories seeded and exits with a message; verify a development farmer and rerun to seed products. The script refuses to run when `ENVIRONMENT=production` and never runs automatically.

## Browser E2E dataset (development only)

For a minimal customer-to-checkout browser flow, start the Compose API and database, then run `python -m scripts.seed_e2e_data` inside the backend container. The runner refuses `ENVIRONMENT=production`; it creates or reuses its accounts using the registration/login APIs, verifies the farmer through the admin verification API, adds the customer's saved address through the address API, and creates or updates one active farmer product through the farmer product API. It does not write application rows directly and is safe to rerun.

Create a local seed admin once using the existing `python -m scripts.create_admin` command and a local password, or use an existing local admin. For this dataset, the prepared local admin is `orb-local-e2e-admin@example.com` with password `OrbLocalAdmin2026!`. Run the fixture runner from an interactive shell in the backend container:

```bash
docker compose up -d backend
docker compose exec -it backend sh
export E2E_ADMIN_EMAIL=orb-local-e2e-admin@example.com
export E2E_ADMIN_PASSWORD='OrbLocalAdmin2026!'
python -m scripts.seed_e2e_data
exit
```

The fixed fixture login credentials are `orb.e2e.customer@example.com` / `OrbE2ECustomer2026!` and `orb.e2e.farmer@example.com` / `OrbE2EFarmer2026!`. They are for local development only. The active product is `ORB E2E Tomatoes` under Vegetables, and the saved address is labeled `ORB E2E`.

To reset the entire Compose development database, run `docker compose down -v`, then `docker compose up -d` and rerun migrations before the E2E seed setup. This removes all local database data in the Compose volume, including other development records; do not use it for any database containing valuable data. The API currently has no customer/farmer account deletion endpoint.

## Customer addresses (Phase 6)

See [`ADDRESSES.md`](../ADDRESSES.md) for address endpoints, ownership, coordinate validation, default-address promotion, and migration details. The customer-only endpoints are documented in generated OpenAPI at `/docs`.

## Customer cart (Phase 7)

See [`CART.md`](../CART.md) for cart APIs, ownership, quantity/stock rules, server-side totals, stale product behavior, and the no-reservation rule. Revision `20260924_0005` adds the cart schema.

## Orders and checkout (Phase 8)

See [`ORDERS.md`](../ORDERS.md) for checkout APIs, stock locking/decrement, snapshot behavior, COD placeholder, initial status, and transaction guarantees. Revision `20260924_0006` adds orders and order lines.
