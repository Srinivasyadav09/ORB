# ORB Frontend–Backend API Map

## Contract status

Phase 8 implements authentication, profiles, marketplace browsing, customer-owned delivery addresses and carts, and transactional customer orders/checkout with Pydantic v2 schemas and OpenAPI. Real payment processing, order fulfillment management, and React integration remain future work. Use UUID strings on the wire; translate to display IDs in the frontend if needed.

Implemented API conventions:

- API prefix `/api`; JSON except image upload.
- Object responses are raw JSON objects; collection responses use `{ "items": [], "page": 1, "page_size": 20, "total": 0, "pages": 0 }`. If choosing an envelope, use it consistently.
- Authenticated endpoints use `Authorization: Bearer <access_token>`; roles/ownership below are server-enforced.
- Error response proposal is FastAPI-compatible `{"detail":"human readable message"}` or structured validation detail. Frontend maps errors to useful screen messages.
- The backend prompt has both `/farmer/...` and `/farmers/...` prefixes in separate sections. This map follows its explicit farmer-order path `/api/farmer/orders` and profile/product paths `/api/farmers/...`; confirm whether to pluralize all routes uniformly.

### Proposed core response shapes

**User/auth:**
```json
{
  "access_token": "<opaque-jwt>",
  "refresh_token": "<opaque-refresh-value-or-cookie>",
  "token_type": "bearer",
  "user": { "id": "uuid", "role": "CUSTOMER", "email": "name@example.test", "full_name": "Example Name", "phone": "+910000000000" }
}
```
Refresh token transport is unresolved; do not put a real secret in examples/config.

**Product list item (implemented; detail also includes `description`):**
```json
{
  "id": "uuid", "name": "Tomatoes", "price": "40.00", "unit": "kg",
  "available_quantity": "25.000", "is_available": true, "status": "ACTIVE",
  "image_url": "https://example.test/tomatoes.jpg",
  "category": {"id": "uuid", "name": "Vegetables"},
  "farmer": {"id": "uuid", "full_name": "Example Farmer", "farm_name": "Example Farm",
    "farm_location": "Hyderabad", "farm_image_url": null, "verification_status": "COMPLETED"},
  "created_at": "2026-09-23T00:00:00Z", "updated_at": "2026-09-23T00:00:00Z"
}
```

**Address:**
```json
{
  "id": "uuid", "label": "Home", "full_name": "Example Name", "phone": "+910000000000",
  "address_line_1": "12 Example Road", "address_line_2": null,
  "city": "Hyderabad", "state": "Telangana", "postal_code": "500001",
  "country": "IN", "latitude": null, "longitude": null, "is_default": true
}
```

**Order:**
```json
{
  "id": "uuid", "order_number": "ORB-2026-0001", "status": "PENDING",
  "payment_status": "PENDING", "payment_method": "COD",
  "subtotal": 80, "delivery_fee": 30, "total": 110,
  "address": { "full_name": "Example Name", "address_line_1": "12 Example Road", "city": "Hyderabad", "state": "Telangana", "postal_code": "500001" },
  "items": [{ "id": "uuid", "product_id": "uuid", "product_name": "Tomatoes", "unit": "kg", "quantity": 2, "unit_price": 40, "line_total": 80 }],
  "created_at": "2026-09-23T00:00:00Z"
}
```

## Phase 5 contract details

All product and category routes use UUIDs. Money and quantity are serialized as fixed-scale decimal strings (price `"45.00"`, quantity `"25.000"`) to avoid binary-float rounding. Accepted units are `kg`, `g`, `bunch`, `piece`, `dozen`, and `litre`. Product image values are optional HTTP(S) URLs or absolute local paths; file uploads and data URLs are rejected.

A product list item has this response shape (product detail adds `description`):

```json
{
  "id": "uuid", "name": "Fresh Tomatoes", "price": "45.00", "unit": "kg",
  "available_quantity": "25.000", "is_available": true, "status": "ACTIVE",
  "image_url": "https://example.test/tomatoes.jpg",
  "category": {"id": "uuid", "name": "Vegetables"},
  "farmer": {"id": "uuid", "full_name": "Example Farmer", "farm_name": "Example Farm",
    "farm_location": "Hyderabad", "farm_image_url": null, "verification_status": "COMPLETED"},
  "created_at": "2026-09-23T00:00:00Z", "updated_at": "2026-09-23T00:00:00Z"
}
```

`POST /api/farmers/me/products` returns 201. A new product defaults to DRAFT; DRAFT or ACTIVE may be supplied, but ACTIVE requires a completed farmer verification. `PATCH` returns 200; unknown/protected fields are rejected with 422, invalid status transitions return 409, unverified publication returns 403, and inaccessible product IDs return 404. `DELETE` returns 200 with the product set to INACTIVE. Category list/detail and marketplace/product detail return 200; missing or inactive public resources return 404. Marketplace query validation (including `min_price <= max_price`, enum sort/status, and page bounds) returns 422.

Product lifecycle transitions are DRAFT → ACTIVE or INACTIVE, ACTIVE → INACTIVE, and INACTIVE → DRAFT or ACTIVE. Re-entering ACTIVE is verification-gated. Quantity is independent from status: ACTIVE with zero quantity remains published with `is_available:false`; `available=true/false` filters by quantity.

## Screen/action mapping

| Frontend screen/action | Method + endpoint | Request body/query | Proposed response body | Auth requirement |
|---|---|---|---|---|
| Customer registration | `POST /api/auth/register/customer` | `{email,password,full_name,phone}` | User/auth response or explicitly chosen registration-only response | Public; creates CUSTOMER user/profile |
| Farmer registration | `POST /api/auth/register/farmer` | `{email,password,full_name,phone,farm_name?,farm_location,farm_description?,farm_image_id}` | User/auth response plus farmer profile/status SUBMITTED | Public; creates FARMER user/profile; image uploaded separately |
| Login | `POST /api/auth/login` | `{email,password}`; role derives from account | Auth response (access token, refresh strategy, safe user) | Public |
| Refresh | `POST /api/auth/refresh` | Refresh cookie or `{refresh_token}` (choose one) | New access/refresh credentials | Refresh credential |
| Restore current user | `GET /api/auth/me` | None | Safe user and role profile summary | Any authenticated role |
| Logout | `POST /api/auth/logout` | Optional refresh-session identifier | `{ "detail": "Logged out" }` or 204 | Any authenticated role |
| Customer account view (**implemented**) | `GET /api/customers/me` | None | `{id,full_name,email,phone,profile_image_url,created_at,updated_at}` | CUSTOMER; Bearer access token |
| Customer account edit (**implemented**) | `PATCH /api/customers/me` | `{full_name?,phone?,profile_image_url?}`; unknown/protected keys rejected | Same customer profile object; email is read-only | CUSTOMER; Bearer access token; authenticated user only |
| Farmer profile view (**implemented**) | `GET /api/farmers/me` | None | `{id,full_name,email,phone,farm_name,farm_location,farm_description,farm_image_url,verification_status,verification_submitted_at,verification_completed_at,created_at,updated_at}` | FARMER; Bearer access token |
| Farmer profile edit (**implemented**) | `PATCH /api/farmers/me` | `{full_name?,farm_name?,phone?,farm_location?,farm_description?,farm_image_url?}`; verification/security fields rejected | Same farmer profile object | FARMER; Bearer access token; authenticated user only |
| Public farmer profile (**implemented**) | `GET /api/farmers/{farmer_id}` | Path UUID | `{id,full_name,farm_name,farm_location,farm_description,farm_image_url,is_verified}`; no phone, email, or timestamps | Public |
| Farmer verification status (**implemented**) | `GET /api/farmers/me/verification` | None | `{status,submitted_at,completed_at,status_message}` | FARMER; Bearer access token |
| Admin verification queue (**implemented**) | `GET /api/admin/farmers` | `page` (default 1), `page_size` (default 20, max 100), optional `status` enum | `{items:[AdminFarmer],page,page_size,total,pages}`; admin items include contact details and verification timestamps, never credentials | ADMIN; Bearer access token |
| Admin farmer detail (**implemented**) | `GET /api/admin/farmers/{farmer_id}` | Path UUID | `AdminFarmer` including contact and farm/verification details, excluding internal account/auth fields | ADMIN; Bearer access token |
| Admin update verification (**implemented**) | `PATCH /api/admin/farmers/{farmer_id}/verification` | `{"status":"VERIFYING"}` (or a valid transition) | `{farmer_id,status,submitted_at,completed_at,status_message}` | ADMIN; Bearer access token |
| Marketplace home/list (**implemented**) | `GET /api/products` | Query: `page` (1), `page_size` (20, max 100), `search`, `category_id` or `category`, `min_price`, `max_price`, `available`, `farmer_id`, `sort` | Paginated `{items:[ProductListItem],page,page_size,total,pages}` | Public; 200, invalid filters 422 |
| Marketplace search/filter/sort (**implemented**) | `GET /api/products` | Search is case-insensitive over name/description/category; sort: `newest`, `oldest`, `price_low`, `price_high`, `name` | Same paginated response; only active-category products from active, verified farmers; includes zero-stock products with `is_available:false` | Public; invalid sort/price range/paging 422 |
| Product detail (**implemented**) | `GET /api/products/{product_id}` | Path UUID | `ProductResponse` with description, Decimal price/quantity strings, category/farmer safe summaries, image URL, status and availability | Public; 404 if not public/active/verified |
| Category list/filter options (**implemented**) | `GET /api/categories` | No query | Raw array of active `CategoryResponse` objects | Public; 200 |
| Category detail (**implemented**) | `GET /api/categories/{category_id}` | Path UUID | `CategoryResponse` `{id,name,description,image_url,is_active,created_at,updated_at}` | Public; 404 for unknown/inactive category |
| Farmer inventory list (**implemented**) | `GET /api/farmers/me/products` | Query `page`, `page_size` (max 100), `status`, `category_id`, `search`, `sort` | Paginated owned `ProductListItem` collection | FARMER Bearer; 401/403; 422 invalid query |
| Add product (**implemented**) | `POST /api/farmers/me/products` | `{name,description?,category_id,price,unit,available_quantity?,image_url?,status?}`; no farmer ID; default DRAFT | `ProductResponse`; status defaults DRAFT; image URL/reference only | FARMER Bearer; 201, 401/403, invalid/inactive category 422, unverified ACTIVE 403 |
| Edit/daily update (**implemented**) | `PATCH /api/farmers/me/products/{product_id}` | Partial name/description/category_id/price/unit/available_quantity/image_url/status | Updated `ProductResponse` | FARMER Bearer; owner only (404 otherwise); invalid data 422; illegal state transition 409; unverified publish 403 |
| Farmer product detail (**implemented**) | `GET /api/farmers/me/products/{product_id}` | Path UUID | Owned `ProductResponse`, any status | FARMER Bearer; 404 outside owner scope |
| Deactivate product (**implemented**) | `DELETE /api/farmers/me/products/{product_id}` | Path UUID | Updated `ProductResponse` with status INACTIVE (soft deactivation) | FARMER Bearer; owner only; 404 outside owner scope |
| Admin product moderation list (**implemented**) | `GET /api/admin/products` | Query `page`, `page_size` (max 100), `status`, `farmer_id`, `category_id` | Paginated `{items:[ProductListItem],page,page_size,total,pages}` | ADMIN Bearer; 401/403; invalid query 422 |
| Admin product detail (**implemented**) | `GET /api/admin/products/{product_id}` | Path UUID | `ProductResponse` for any product state | ADMIN Bearer; 401/403/404 |
| Product image upload | `POST /api/uploads/image` | Multipart `file` | `{file_id,url,filename,content_type,size}` | Authenticated CUSTOMER/FARMER; allowed role/ownership refined per use |
| Farm/profile image upload | `POST /api/uploads/image` | Multipart `file` | File metadata and stable URL/reference | FARMER |
| Cart view (**implemented**) | `GET /api/cart` | None | `{id,items:[{id,product_id,product_name,product_image_url,unit,unit_price,quantity,available_stock,line_total,is_available,availability_reason}],item_count,subtotal}` | CUSTOMER Bearer; lazily creates one cart |
| Add cart item (**implemented**) | `POST /api/cart/items` | `{product_id,quantity}`; no client price, stock, owner, or totals | Updated `CartResponse`; repeated adds increase quantity | CUSTOMER Bearer; 409 unavailable/over stock |
| Change cart quantity (**implemented**) | `PATCH /api/cart/items/{product_id}` | `{quantity}` positive integer | Updated `CartResponse` with current prices/totals | CUSTOMER Bearer; 404 if no owned line; 409 unavailable/over stock |
| Remove cart item (**implemented**) | `DELETE /api/cart/items/{product_id}` | None | 204 | CUSTOMER Bearer; only own cart line |
| Clear cart (**implemented**) | `DELETE /api/cart` | None | 204; cart remains | CUSTOMER Bearer; products/inventory remain untouched |
| Saved-address list (**implemented**) | `GET /api/addresses` | No query | Raw array of owned `AddressResponse` objects | CUSTOMER Bearer; 401/403 |
| Add manual address (**implemented**) | `POST /api/addresses` | Required contact/address fields; coordinates optional as a pair | `AddressResponse`; 201 | CUSTOMER Bearer; ownership derived from token; 422 invalid fields |
| Address detail/edit/delete (**implemented**) | `GET/PATCH/DELETE /api/addresses/{address_id}` | PATCH partial fields; customer ID and timestamps are forbidden | Address / 204 | CUSTOMER Bearer; foreign IDs return 404 |
| Get default address (**implemented**) | `GET /api/addresses/default` | No query | `AddressResponse`; 404 if unset | CUSTOMER Bearer |
| Set default address (**implemented**) | `PATCH /api/addresses/{address_id}/default` | No body | Updated `AddressResponse` | CUSTOMER Bearer; owner only; 404 otherwise |
| “Current location” | No endpoint until browser geolocation exists; save via `POST /api/addresses` | Only after browser permission, send address and optional lat/lng | Created Address | CUSTOMER |
| Checkout/place order (**implemented**) | `POST /api/orders` | `{address_id,payment_method?}`; no client prices/totals | Order with immutable delivery/product snapshots, server totals, COD/PENDING, CONFIRMED | CUSTOMER Bearer; 409 empty cart/unavailable/insufficient stock; 404 unowned address |
| Customer order history (**implemented**) | `GET /api/orders` | `page` (1), `page_size` (20, max 100) | Paginated owned `OrderListItem` collection | CUSTOMER Bearer |
| Customer order detail (**implemented**) | `GET /api/orders/{order_id}` | Path UUID | Owned order with snapshots and order items | CUSTOMER Bearer; foreign IDs return 404 |
| Farmer order list | `GET /api/farmer/orders` | Page/page_size/status | Paginated orders containing farmer-owned items | FARMER |
| Farmer order detail | `GET /api/farmer/orders/{order_id}` | Path UUID | Order detail restricted to farmer's lines and necessary delivery data | FARMER, associated farmer only |
| Farmer updates fulfillment status | `PATCH /api/farmer/orders/{order_id}/status` | `{status}` from allowed transition set | Updated status/timestamps | FARMER, associated farmer only |
| Customer rates delivered item | `POST /api/orders/{order_id}/ratings` | `{product_id,rating,review?}` | Created Rating `{id,order_id,product_id,rating,review,created_at}` | CUSTOMER, order owner; delivered and item membership required |
| Product ratings | `GET /api/products/{product_id}/ratings` | Page/page_size | `{items:[Rating],rating_average,rating_count,...}` | Public |
| Notification list/bell | `GET /api/notifications` | `unread_only,page,page_size` | `{items:[Notification],unread_count,...}` | Any authenticated role, own notifications |
| Mark notification read | `PATCH /api/notifications/{notification_id}/read` | None or `{is_read:true}` | Updated Notification | Authenticated owner |
| Mark all read | `PATCH /api/notifications/read-all` | None | `{updated_count}` | Authenticated user |
| Service health | `GET /health` | None | `{status:"ok"}` | Public/infra |
| Database health | `GET /health/db` | None | `{status:"ok"}` or service-unavailable response | Public/infra; no DSN detail |

## Contract decisions required for future APIs

The implemented Phase 3–5 contracts are fixed by their Pydantic schemas and OpenAPI. These decisions concern future APIs only.

1. Confirm raw object/list versus `{data:...}` response envelope. This map proposes raw object and paginated `{items,...}` collections.
2. Confirm email/password login body versus OAuth2 form `username` and refresh-token transport. Do not implement a client against an unconfirmed token shape.
3. Confirm plural farmer path convention: profile/product routes use `/farmers`, while specified farmer-order routes use `/farmer`.
4. Confirm whether profile image upload may be called before registration or registration accepts multipart; the map proposes upload first then send `image_id`.
6. Confirm canonical order transitions and map to UI labels; confirm payment method/status and delivery fee rules.
7. Confirm order create body reads the persistent cart or carries line items; this map proposes server cart as source of truth.
8. Confirm currency symbol/display and future cart/order quantity conversion rules.
9. Decide notification list UI and unread count surface.
10. Define public/private farmer and customer fields and delivery PII exposure for multi-farmer orders.
11. Ensure mock localStorage migration handles non-UUID IDs, stale product snapshots and Data URL images.
