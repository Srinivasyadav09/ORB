# ORB Orders and Checkout (Phase 8)

## Customer APIs

| Method | Path | Behavior |
|---|---|---|
| `POST` | `/api/orders` | Create an order from the authenticated customer's cart and selected saved address (201) |
| `GET` | `/api/orders` | List the customer's orders, newest first; page/page_size pagination |
| `GET` | `/api/orders/{order_id}` | Retrieve one owned order with address and line snapshots |

All routes require an authenticated `CUSTOMER` bearer token. Customer identity is derived from the token. Foreign and missing order/address identifiers return 404. There is no customer status-update or cancellation route.

## Checkout and snapshots

Checkout accepts only `address_id` and optional `payment_method` (`COD`). It rejects an empty cart, verifies that the saved address belongs to the customer, and copies the address fields and optional coordinates into the order. Each line snapshots the current server product name, image, unit, farmer ID, price, quantity, and line total. Later address/product edits or deletion do not rewrite these snapshots; product and farmer foreign keys may become null while snapshot fields remain.

Money uses `Decimal`/`NUMERIC`; checkout calculates each line as current product price times cart quantity, sums the subtotal, applies a server-defined delivery fee of `0.00 INR`, and records the total. Successful orders start as `CONFIRMED`. Payment is represented as `COD` with `PENDING` status; no payment is processed.

Order numbers are generated server-side as `ORB-YYYYMMDD-<10 uppercase hex characters>` and protected by a database unique constraint.

## Inventory and atomicity

Cart contents do not reserve stock. Checkout locks the customer's row and cart, then locks all product rows in UUID order. It reuses Phase 5/7 marketplace availability rules and checks current stock. Within one database transaction it snapshots the address/products, creates the order and lines, decrements inventory, and clears cart items. Any validation/database failure leaves the order, stock, and cart unchanged. The product table's nonnegative-stock check is a final guard against negative inventory.

## Known limitations

Delivery fee is currently zero. Only COD is supported, with no payment processing. Order status begins at `CONFIRMED`; fulfillment/admin status workflows and cancellation are not provided in this phase. Order history uses page/page_size pagination.
