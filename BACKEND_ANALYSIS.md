# ORB — Online Raithu Bazaar: Backend Analysis

## Scope and evidence

This is a Phase 1 analysis of the existing React + Vite frontend. The workspace contains `orb-web/` and no backend directory, FastAPI source, OpenAPI specification, or database schema. Frontend mock structures are documented as observed UI models; the request/response bodies proposed in `FRONTEND_BACKEND_API_MAP.md` are integration proposals and must become the agreed Pydantic/OpenAPI contract before implementation.

No React files, data, styles, or runtime behavior were modified for this analysis. No backend or database objects were created.

## Existing frontend architecture

- Vite, React 19, JavaScript/JSX, React Router 7, and Lucide icons. `orb-web/package.json` has only dev/build/preview scripts and no test, lint, or TypeScript build script.
- `src/app/App.jsx` routes public auth, customer shopping/account/orders, and farmer dashboard/inventory/profile/verification/orders pages. `RequireRole` gates customer/farmer route trees based on client-side auth state only.
- Reusable UI is under `src/components/`; screens under `src/pages/`; role layouts under `src/components/layout/`.
- Contexts under `src/context/` split auth, customer, farmer, products, cart, orders, addresses, ratings, and notifications. Most are mock/localStorage domains, not API-backed.
- Seed data is under `src/data/`; guarded JSON browser storage is under `src/utils/storage.js`.
- `src/services/api/` has a fetch client, service stubs, a normalizer, and a declaration file. These services are not used by the contexts or screens. Some paths and mock DTOs in those stubs are not aligned with the backend prompt's route inventory; they are scaffolding rather than a verified contract. `src/config/env.js` reads Vite environment values.
- Loading/empty UI primitives exist, but data contexts do not expose remote loading/error states. Several pages render seed data directly.

## Observed data models and persistence

| Entity/domain | Observed frontend shape | Storage/source |
|---|---|---|
| Auth session | `{ role, profile }`; role is `customer` or `farmer`; profile includes `fullName`, `phone`, `email`; farmer registration adds `location`, `farmImage` | `orb-demo-session` in local storage; legacy session-storage migration. API client token key is `orb-auth-token`, but the auth flow does not obtain a backend token. |
| Customer profile | Generic profile object with `fullName`, `phone`, `email` | `orb-customer-profile`; initially migrated from the local auth profile. |
| Farmer | `fullName`, `phone`, `email`, `location`, `farmName`, `farmImage`, `verification`, `submittedAt`, `completedAt` | `orb-farmer-data.profile`; initial sample profile in `FarmerContext`. |
| Product | `id`, `name`, `category`, `price`, `unit`, `qty`, `image`, `description`, `farmer`, `farmerLocation`, `farmerVerified`, `farmerBio`, `rating`, `reviews`, `active`, `createdAt`, `updatedAt` | Eight market seeds in `src/data/products.js`; `orb-products`; farmer list in `orb-farmer-data.products`. |
| Category | Display strings such as Vegetables, Fruits, Leafy Greens, Grains, Dairy, Other | Hard-coded filter/form option arrays; no category entity or ID. |
| Cart | Array `{ product: ProductSnapshot, qty }`; subtotal/count derived in context/page | `orb-customer-cart`; customer-only UI. |
| Address | `id`, `label`, `fullName`, `phone`, `line1`, `city`, `state`, `postalCode`, `isDefault` | Seeds in `src/data/addresses.js`; `orb-customer-addresses`; selected ID in `orb-selected-address`. |
| Customer order | `id`, display `date`, `status`, `subtotal`, `deliveryFee`, `total`, `paymentMethod`, `addressId`, address snapshot, item product ID/snapshot, `quantity`, `unitPrice`, `rating`, `review` | Seeded in `src/data/orders.js`; `orb-customer-orders`. |
| Farmer order | `id`, date, `customer`, phone, delivery-address string, status, item name/quantity/unit/price/image, total | Seeded in `OrdersContext`; `orb-farmer-orders` or legacy `orb-farmer-data.orders`. |
| Rating | Order ID, product ID, integer score, optional review, timestamp; order item gets `rating` and `review` | `orb-ratings` and embedded customer order item. |
| Notification | `id`, `message`, `type`, `createdAt`, `read` | In-memory only; header renders a bell but no notification list. |
| Uploaded image | File read into browser Data URL; product/farmer model stores that string as `image`/`farmImage` | Browser local storage only; initial seed images are remote Unsplash URLs. |
| Payment | Choice string (`UPI / Card / Net Banking` or `Cash on Delivery`) | Checkout component state; no payment status or provider integration in frontend. |

IDs in seed data are mixed numeric/string values; backend UUIDs will require frontend normalization and a local-storage migration/clear strategy.

## Backend entities required

1. `User` and `RefreshToken` (or revocable token/session record).
2. `Customer` and `Farmer` one-to-one role profiles.
3. `Category`, `Product`, `Image`/file metadata, and optionally `ProductImage` if multiple images are supported.
4. `Address` and `Cart`/`CartItem`.
5. `Order`/`OrderItem` snapshots and payment status.
6. `Rating` with links to customer, order item, and product.
7. `Notification` owned by a user.

Admin uses the `User` role and farmer verification permissions; a separate admin profile is not required for this initial scope.

## Business rules and validation requirements

### Accounts/authentication

- Customer and farmer registration create `User` plus the corresponding profile in one transaction. Normalize and uniquely constrain email; validate phone; never serialize password hashes.
- Hash passwords with Argon2 or bcrypt. Login issues short-lived access tokens and refresh credentials with rotation/revocation. Logout revokes the refresh session. `/auth/me` returns the authenticated role/profile.
- Backend role checks are authoritative. A route guard in React is only navigation UX.

### Customer/profile/address

- A customer can read/update only their own profile and addresses.
- Require a valid full name, phone, address line, city, state, postal code; allow line 2, country, coordinates and label. Address CRUD and default-address selection must be customer-scoped; enforce at most one default address per customer.
- “Use current location” currently selects a hard-coded mock Hyderabad address; no `navigator.geolocation` is called. If real location is implemented, permission/request belongs to the browser, with coordinates submitted only after consent.

### Farmer/verification

- Farmer profile exposes farm location/description, image/profile image, status and timestamps. Farmer can edit allowed profile fields but cannot set verification status.
- Proposed statuses from the backend request: SUBMITTED, VERIFYING, COMPLETED, REJECTED. Only ADMIN can change status; audit who changed it and when. Define rejection reason and resubmission policy.
- Product publishing should require COMPLETED verification per backend request. Current frontend lets a farmer reach product creation regardless of status; integration must display a useful blocked/draft state.

### Products/categories/images/inventory

- Products belong to one farmer and category; price uses positive Decimal money, available quantity uses non-negative Decimal units, and product status is DRAFT/ACTIVE/INACTIVE. Availability is derived from ACTIVE status and quantity greater than zero; zero quantity does not erase publication status. The Phase 5 API uses the frontend units kg, g, bunch, piece, dozen, and litre.
- Only the owning farmer can read/mutate their inventory endpoints; public marketplace exposes active, available products and safe farmer summary data.
- Search/category/farmer/min/max price/availability/sort/pagination are database-side filters. Phase 5 uses PostgreSQL trigram indexes for case-insensitive name/description/category substring search, bounded page/page_size, and a fixed sort whitelist.
- Quantity/price/availability updates must be persisted; enforce inventory bounds and serialize concurrent stock changes.
- Upload validates actual content type and size, generates safe names, stores outside source, and returns a stable file ID/URL. Product/farmer rows keep a file reference or URL, not a Data URL. Do not trust the original filename.

### Cart/checkout/orders/payment

- Cart is per customer. Item quantity must be positive and not exceed available stock. Revalidate product active state and quantity on each mutation/checkout.
- Never trust frontend product price, subtotal, delivery fee, total, farmer ID or payment result. The server reloads prices, calculates totals/fees, snapshots address and product data, then commits order/items and stock decrement in a transaction.
- Use database row locks/conditional stock updates to prevent overselling. Clear purchased cart items atomically after successful order creation. Add an idempotency key or equivalent retry protection to prevent duplicate checkout orders.
- Persist separate order and payment statuses. Backend prompt statuses differ from current UI: UI uses Processing/Shipped/Delivered/Cancelled; proposed backend order statuses are PENDING/CONFIRMED/PREPARING/READY_FOR_DELIVERY/OUT_FOR_DELIVERY/DELIVERED/CANCELLED. Provide a display mapping and legal transition table.
- Payment is currently a placeholder. Use a payment-service abstraction; initially allow COD and a mock digital result only. Never store card/CVV/bank credentials. Define payment-state transitions and refunds before enabling real digital payments.
- Farmer order access must only include orders with items from that farmer; delivery/contact information should be disclosed only to authorized parties.

### Ratings/notifications

- Rating 1–5, optional length-limited review. Customer must own the order; order must be delivered; product must occur in that order; one rating per customer/order/product. Update aggregates from stored ratings, not client submissions.
- Notifications are user-scoped. Generate order/verification events transactionally with their domain change where possible. Support read-one/read-all and unread count. Current UI has no panel/empty/error view.

## Authentication design proposal

- `POST /api/auth/register/customer` and `/api/auth/register/farmer` use dedicated Pydantic request models.
- `POST /api/auth/login` verifies password hash and returns an access token plus refresh token/secure cookie according to the agreed client strategy. `POST /api/auth/refresh` rotates refresh credentials; `POST /api/auth/logout` revokes the session. `GET /api/auth/me` returns safe user/profile data.
- Keep JWT secret/algorithm/expiry and cookie settings in environment configuration. Access tokens travel in `Authorization: Bearer …`; never store password or refresh-token secrets in logs. Prefer HttpOnly, Secure, SameSite refresh cookies for production and CSRF controls if cookies are used.
- Define CORS allowlist for the React origin; return structured 401/403/422 errors. On 401 frontend clears stale auth and requires login.

## Authorization design proposal

- Roles: CUSTOMER, FARMER, ADMIN. Reusable dependencies resolve current active user and enforce role.
- Customer can access only own profile, address, cart, orders, ratings and notifications.
- Farmer can access own profile, verification read state, own products and own order slices. Farmer cannot update verification status or another farmer's product/order.
- Admin-only verification transition and future administrative views. Public routes are limited to marketplace/category/product/farmer public profiles and health.
- Check both role and resource ownership in service/repository operations; do not trust client-supplied customer/farmer IDs.

## Proposed relationships

- User 1:0..1 Customer; User 1:0..1 Farmer; User 1:N Notification and refresh sessions.
- Farmer 1:N Product; Category 1:N Product; Product 1:N ProductImage/Image association, OrderItem and Rating.
- Customer 1:N Address, 1:1 Cart, 1:N Order and Rating.
- Cart 1:N CartItem; CartItem references Product and is unique per cart/product.
- Order 1:N OrderItem; Order stores customer FK and immutable delivery-address snapshot. OrderItem stores immutable product name, unit, unit-price and farmer snapshot to preserve history after catalog edits.
- Rating references customer, order item/order, product; unique customer/order-item or customer/order/product constraint.
- Image metadata records uploader, generated storage key, URL, MIME type and byte size. Refresh session stores a hashed token identifier, expiry and revoked timestamp.

## Proposed implementation order

1. Freeze endpoint request/response schemas and status mappings; resolve the open questions in `FRONTEND_BACKEND_API_MAP.md`.
2. FastAPI skeleton, settings, health endpoints, async DB session, PostgreSQL, Docker Compose, Alembic and structured errors.
3. User/auth/password/JWT/refresh/logout and role dependencies.
4. Customer/farmer profiles and admin verification foundation.
5. Categories and products, marketplace query/pagination, farmer inventory ownership.
6. Image upload service and metadata.
7. Addresses/defaults.
8. Cart validation and persistence.
9. Transactional checkout/orders, inventory safety, notifications and payment abstraction.
10. Ratings/aggregates and notification read APIs.
11. Isolated pytest/httpx coverage, seed script, docs, migrations, Docker/local verification.
12. Frontend adapter/context integration with loading/error/empty states and local-storage migration.

## Risks and ambiguities

- No backend source/OpenAPI exists yet, so JSON field names, response envelope, error body and auth token transport must be agreed before client integration.
- Backend UUID IDs conflict with numeric seed IDs and strings like `ORB00123`; order public number may need a separate display identifier.
- Proposed backend order states and frontend states need a transition/display mapping. Verification `REJECTED` is not represented in UI.
- Current generic digital payment choice, fixed delivery charge, payment status and cancellation/refund behavior are underspecified.
- Farmer registration asks for a farm image but backend model distinguishes farm image/profile image and image upload; decide multipart sequencing and whether application can be submitted before verification.
- Current farmer product seeds overlap market seeds and current seed ownership is inconsistent; choose a deterministic development seed plan.
- Customer/farmer dashboard summaries and average rating are hard-coded mock values; decide whether API summary endpoints are useful or derive from paginated records.
- Notification API has no notification UI surface. Decide the first frontend presentation and update behavior.
- Address “current location” is mock-only. Do not silently introduce browser location permission.
- Categories are strings in the UI. Define stable IDs/slugs and category seeding.
- Local storage contains stale demo credentials, cart snapshots, IDs, and image Data URLs; integration needs a safe migration/clear/versioning approach.
- The existing API service stubs are not wired to app state and include unverified endpoints/DTO assumptions; reconcile them to the final OpenAPI contract before enabling live mode.
