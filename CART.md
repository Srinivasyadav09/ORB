# ORB Customer Cart (Phase 7)

The backend keeps one lazily created cart per customer. Every operation derives the customer from the authenticated user and requires the `CUSTOMER` role. No request accepts cart/customer ownership, farmer IDs, prices, totals, or stock values.

## API

| Method | Path | Result |
|---|---|---|
| `GET` | `/api/cart` | Current cart; creates and returns an empty cart on first access |
| `POST` | `/api/cart/items` | Add `{product_id, quantity}` or increase the existing line; returns the cart |
| `PATCH` | `/api/cart/items/{product_id}` | Set `{quantity}` on an existing line; returns the cart |
| `DELETE` | `/api/cart/items/{product_id}` | Remove one owned line (204) |
| `DELETE` | `/api/cart` | Remove all lines while keeping the cart (204) |

Quantities must be positive integers. Add and update re-read the product under a row lock and require it to be active, in stock, in an active category, offered by a verified farmer, and owned by an active farmer account. Missing products/cart lines return 404; unavailable products and requests above stock return 409. Cart lines are unique per product and cart.

## Prices, stock, and stale cart items

Unit price comes from the current product record. Line totals, cart subtotal, delivery fee, and total use `Decimal`; money is serialized to two decimal places and product stock to three. `item_count` is the sum of line quantities. GET returns current product name/image/unit/price/stock and an availability flag/reason. It does not silently remove items whose products later become unavailable. The current backend delivery fee is INR 0.00; the cart response includes `delivery_fee` and `total_amount` using the same calculation as order creation.

Adding a product to a cart does **not** reserve or decrement inventory. Cart reads and updates do not change product stock. Checkout stock reservation and decrement are outside this phase.

## Persistence and concurrency

Revision `20260924_0005` creates `carts` and `cart_items`. A unique customer constraint enforces one cart per customer; a cart/product unique constraint prevents duplicate lines; a positive-quantity check protects persisted rows. The service locks the customer row to serialize lazy cart creation and cart mutations, and locks products while validating add/update stock.

## Known limitations

Cart reads are not paginated. Current price is shown, not snapshotted; the future order phase must snapshot price at checkout. Unavailable cart lines are surfaced but require the customer to remove or adjust them manually.
