# ORB Product Catalog and Marketplace (Phase 5)

Phase 5 implements categories, product records, farmer inventory management, the public marketplace, and read-only admin product moderation. Cart, orders, ratings, uploads, and payments are not implemented here.

## Product fields and units

Products use UUIDs and belong to exactly one farmer profile and one category. The category and farmer references are foreign keys. Products keep one optional `image_url`; this matches the current frontend's single product image. Values may be HTTP(S) URLs or absolute local paths up to 2048 characters. Data URLs and file uploads are rejected. Phase 11 will add upload handling and stable file references.

Price is stored as PostgreSQL `NUMERIC(12,2)` and quantity as `NUMERIC(12,3)`; Python and Pydantic use `Decimal`. JSON responses serialize those as fixed-scale strings (for example `"45.00"` and `"2.500"`). Prices must be greater than zero; quantity may be zero but never negative. Supported units match the current product form: `kg`, `g`, `bunch`, `piece`, `dozen`, and `litre`. Quantity values are interpreted in the product's declared unit; conversions between units are not performed.

Categories have a unique case-insensitive name, optional description/image reference, active flag, and timestamps. Public list/detail APIs show only active categories. Category creation/administration is seed/database work in this phase; no category write endpoint is exposed.

## Lifecycle, visibility, and ownership

Stored product status is `DRAFT`, `ACTIVE`, or `INACTIVE`. `OUT_OF_STOCK` is not a stored status because stock is an independent inventory value:

| Current status | Allowed next status |
|---|---|
| DRAFT | ACTIVE, INACTIVE |
| ACTIVE | INACTIVE |
| INACTIVE | DRAFT, ACTIVE |

New products default to DRAFT. New records may be explicitly created as ACTIVE only by a completed farmer; an unverified farmer may create/edit drafts but cannot publish. Any transition to ACTIVE requires `verification_status=COMPLETED`. A state outside the allowed transition table returns 409; an unknown enum or invalid create state returns 422.

A public product must be ACTIVE, belong to an active category, and be owned by an active farmer with completed verification. Draft and inactive products are hidden from public listing/detail routes. Product ownership is derived from the authenticated farmer; request bodies cannot supply owner IDs. Farmer reads and mutations scope the query by both product ID and the farmer profile ID, returning 404 for another farmer's product.

`DELETE /api/farmers/me/products/{product_id}` is a soft deactivation. It sets status to INACTIVE and keeps the record and foreign keys for future order history. Repeating DELETE is safe. Admins can list and read products for moderation but cannot mutate product status in this phase.

## Inventory and availability

`available_quantity` is a non-negative Decimal independent from status. An ACTIVE item whose quantity is zero remains published and is returned with `is_available: false`. The marketplace can filter with `available=true` or `available=false`. `is_available` is true only when status is ACTIVE and quantity is greater than zero. This preserves the publication state when stock runs out; later cart/checkout phases must reject zero stock and recheck stock transactionally.

Updating daily quantity to zero does not change status. Restocking an active product makes it available again. Marking a product unavailable is represented by moving it to INACTIVE; re-publication uses INACTIVE → ACTIVE and still requires completed farmer verification.

## Marketplace queries

`GET /api/products` is public and paginated (`page` starts at 1; `page_size` defaults to 20 and is capped at 100). It supports:

- `search`: case-insensitive substring search over product name, description, and category name. `%` and `_` are escaped as literal characters.
- `category_id` or exact case-insensitive `category` name.
- `min_price`, `max_price` (Decimal, non-negative; minimum cannot exceed maximum).
- `available=true|false` based on quantity.
- `farmer_id` for a public seller filter.
- `sort=newest|oldest|price_low|price_high|name`.

Unsupported sort values, invalid UUIDs, out-of-range paging, and invalid price ranges return 422. Filters, ordering, count, and pagination execute in PostgreSQL. A page query eager-loads category and farmer relationships with `selectinload`; it does not fetch related rows once per product.

Product detail returns the description plus category and safe farmer summary (`id`, name, farm name/location/image, verification state). It never includes a farmer's email, phone, account status, or credentials. Product list items omit only the description.

## API overview

| Method and path | Authentication | Success |
|---|---|---|
| `GET /api/categories` | Public | 200, active category array |
| `GET /api/categories/{category_id}` | Public | 200; 404 if missing/inactive |
| `GET /api/products` | Public | 200, paginated public products |
| `GET /api/products/{product_id}` | Public | 200; 404 if not publicly visible |
| `GET /api/farmers/me/products` | FARMER Bearer | 200, own paginated inventory |
| `POST /api/farmers/me/products` | FARMER Bearer | 201; default DRAFT |
| `GET /api/farmers/me/products/{product_id}` | FARMER Bearer | 200; 404 outside owner scope |
| `PATCH /api/farmers/me/products/{product_id}` | FARMER Bearer | 200; 404 outside owner scope, 409 invalid transition |
| `DELETE /api/farmers/me/products/{product_id}` | FARMER Bearer | 200 with status INACTIVE |
| `GET /api/admin/products` | ADMIN Bearer | 200, paginated/filterable moderation list |
| `GET /api/admin/products/{product_id}` | ADMIN Bearer | 200; 404 if missing |

Farmer creation body:

```json
{
  "name": "Fresh Tomatoes",
  "description": "Harvested this morning",
  "category_id": "7f63f5d9-32d9-4a22-a9de-d946d55b29b6",
  "price": "45.00",
  "unit": "kg",
  "available_quantity": "25.000",
  "image_url": "https://example.test/tomatoes.jpg",
  "status": "DRAFT"
}
```

Farmer product list accepts `page`, `page_size`, `status`, `category_id`, `search`, and `sort`. Admin product listing accepts `page`, `page_size`, `status`, `farmer_id`, and `category_id`. Admin product access is read-only.

## Database indexes and migration

Revision `20260923_0003` creates product/category tables and enums, foreign keys, check constraints, and indexes. Owner, category, status, creation time, and price indexes support the endpoint's scope/filter/order patterns. Case-insensitive substring search uses PostgreSQL `pg_trgm` GIN indexes for product names/descriptions and category names. A functional unique index on `lower(categories.name)` prevents case-only duplicate categories. Products retain foreign keys with RESTRICT behavior so deactivation, rather than hard deletion, preserves future references.

## Development data

`python -m scripts.seed_marketplace` is opt-in, refuses `ENVIRONMENT=production`, and creates the documented category list. It adds seven fake active products only for an existing farmer whose verification status is COMPLETED. It does not create or auto-verify a farmer, create credentials, or run at application startup.
