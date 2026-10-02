from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.models.cart import Cart
from app.models.customer import Customer
from app.models.product import Product, ProductStatus
from tests.test_products import create_public_product
from tests.test_profiles import bearer, register


def cart_headers(token):
    return bearer(token)


async def add_item(client, token, product_id, quantity=1, **extra):
    payload = {"product_id": str(product_id), "quantity": quantity, **extra}
    return await client.post(
        "/api/cart/items", headers=cart_headers(token), json=payload
    )


async def set_product_fields(context, product_id, **fields):
    async with context["session_factory"]() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        assert product is not None
        for field, value in fields.items():
            setattr(product, field, value)
        await session.commit()


async def product_stock(context, product_id):
    async with context["session_factory"]() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        assert product is not None
        return product.available_quantity


@pytest.mark.asyncio
async def test_customer_gets_lazy_empty_cart_and_exactly_one_cart(auth_test_context):
    client = auth_test_context["client"]
    customer_token, customer_user = await register(client, "CUSTOMER")
    first = await client.get("/api/cart", headers=cart_headers(customer_token))
    second = await client.get("/api/cart", headers=cart_headers(customer_token))
    assert first.status_code == 200 and first.json()["items"] == []
    assert first.json()["item_count"] == 0 and first.json()["subtotal"] == "0.00"
    assert first.json()["delivery_fee"] == "0.00"
    assert first.json()["total_amount"] == "0.00"
    assert second.json()["id"] == first.json()["id"]

    async with auth_test_context["session_factory"]() as session:
        customer = await session.scalar(
            select(Customer).where(Customer.user_id == UUID(customer_user["id"]))
        )
        assert customer is not None
        carts = list(
            (
                await session.scalars(
                    select(Cart).where(Cart.customer_id == customer.id)
                )
            ).all()
        )
        assert len(carts) == 1 and str(carts[0].id) == first.json()["id"]


@pytest.mark.asyncio
async def test_customer_adds_products_duplicate_add_increases_quantity_and_totals_use_server_prices(
    auth_test_context,
):
    client = auth_test_context["client"]
    customer_token, _ = await register(client, "CUSTOMER")
    _, _, _, first = await create_public_product(
        auth_test_context,
        name=f"Cart Tomatoes {uuid4().hex[:6]}",
        price="12.50",
        quantity="10",
    )
    _, _, _, second = await create_public_product(
        auth_test_context,
        name=f"Cart Apples {uuid4().hex[:6]}",
        price="20.00",
        quantity="8",
    )

    added = await add_item(client, customer_token, first["id"], 2)
    assert added.status_code == 200, added.text
    duplicate = await add_item(client, customer_token, first["id"], 3)
    assert duplicate.status_code == 200, duplicate.text
    another = await add_item(client, customer_token, second["id"], 1)
    assert another.status_code == 200, another.text
    cart = (await client.get("/api/cart", headers=cart_headers(customer_token))).json()
    assert len(cart["items"]) == 2
    assert cart["item_count"] == 6
    assert cart["subtotal"] == "82.50"
    assert cart["delivery_fee"] == "0.00"
    assert cart["total_amount"] == "82.50"
    assert Decimal(cart["total_amount"]) == (
        Decimal(cart["subtotal"]) + Decimal(cart["delivery_fee"])
    )
    tomato = next(item for item in cart["items"] if item["product_id"] == first["id"])
    assert tomato["quantity"] == 5
    assert tomato["unit_price"] == "12.50"
    assert tomato["line_total"] == "62.50"
    assert tomato["available_stock"] == "10.000"
    assert tomato["is_available"] is True
    assert await product_stock(auth_test_context, UUID(first["id"])) == Decimal(
        "10.000"
    )


@pytest.mark.asyncio
async def test_quantity_update_stock_checks_remove_and_clear_do_not_change_products(
    auth_test_context,
):
    client = auth_test_context["client"]
    customer_token, _ = await register(client, "CUSTOMER")
    _, _, _, first = await create_public_product(
        auth_test_context,
        name=f"Cart Pears {uuid4().hex[:6]}",
        price="9.75",
        quantity="10",
    )
    _, _, _, second = await create_public_product(
        auth_test_context,
        name=f"Cart Plums {uuid4().hex[:6]}",
        price="7.00",
        quantity="6",
    )
    assert (await add_item(client, customer_token, first["id"], 2)).status_code == 200
    updated = await client.patch(
        f"/api/cart/items/{first['id']}",
        headers=cart_headers(customer_token),
        json={"quantity": 5},
    )
    assert updated.status_code == 200
    assert updated.json()["items"][0]["quantity"] == 5
    assert updated.json()["items"][0]["line_total"] == "48.75"
    assert (await add_item(client, customer_token, first["id"], 6)).status_code == 409
    assert (
        await client.patch(
            f"/api/cart/items/{first['id']}",
            headers=cart_headers(customer_token),
            json={"quantity": 11},
        )
    ).status_code == 409
    assert (await add_item(client, customer_token, second["id"], 1)).status_code == 200

    before = await product_stock(auth_test_context, UUID(first["id"]))
    removed = await client.delete(
        f"/api/cart/items/{first['id']}", headers=cart_headers(customer_token)
    )
    assert removed.status_code == 204
    assert await product_stock(auth_test_context, UUID(first["id"])) == before
    cleared = await client.delete("/api/cart", headers=cart_headers(customer_token))
    assert cleared.status_code == 204
    empty = await client.get("/api/cart", headers=cart_headers(customer_token))
    assert empty.status_code == 200 and empty.json()["items"] == []
    assert await product_stock(auth_test_context, UUID(second["id"])) == Decimal(
        "6.000"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("quantity", [0, -1, 1.5, True])
async def test_cart_quantity_must_be_a_positive_integer(auth_test_context, quantity):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    response = await client.post(
        "/api/cart/items",
        headers=cart_headers(token),
        json={"product_id": str(uuid4()), "quantity": quantity},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_cart_rejects_untrusted_fields_and_nonexistent_products(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    product_id = uuid4()
    for fields in (
        {"price": "0.01"},
        {"unit_price": "0.01"},
        {"subtotal": "0.01"},
        {"line_total": "0.01"},
        {"available_stock": 100},
        {"farmer_id": str(uuid4())},
        {"customer_id": str(uuid4())},
        {"cart_id": str(uuid4())},
    ):
        response = await add_item(client, token, product_id, 1, **fields)
        assert response.status_code == 422
    assert (await add_item(client, token, uuid4(), 1)).status_code == 404


@pytest.mark.asyncio
async def test_stock_is_rechecked_when_updating_and_duplicate_add_is_atomic(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    _, _, _, product = await create_public_product(
        auth_test_context, name=f"Stock Check {uuid4().hex[:6]}", quantity="5"
    )
    assert (await add_item(client, token, product["id"], 4)).status_code == 200
    await set_product_fields(
        auth_test_context, UUID(product["id"]), available_quantity=Decimal("2")
    )
    response = await client.patch(
        f"/api/cart/items/{product['id']}",
        headers=cart_headers(token),
        json={"quantity": 4},
    )
    assert response.status_code == 409
    cart = (await client.get("/api/cart", headers=cart_headers(token))).json()
    assert cart["items"][0]["available_stock"] == "2.000"
    assert cart["items"][0]["quantity"] == 4
    assert cart["items"][0]["is_available"] is True


@pytest.mark.asyncio
async def test_unavailable_products_are_rejected_but_stale_items_remain_visible(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    _, _, _, draft = await create_public_product(
        auth_test_context,
        name=f"Draft Item {uuid4().hex[:6]}",
        quantity="4",
        status="DRAFT",
    )
    assert (await add_item(client, token, draft["id"], 1)).status_code == 409

    _, _, _, product = await create_public_product(
        auth_test_context, name=f"Turns Inactive {uuid4().hex[:6]}", quantity="4"
    )
    assert (await add_item(client, token, product["id"], 1)).status_code == 200
    await set_product_fields(
        auth_test_context, UUID(product["id"]), status=ProductStatus.INACTIVE
    )
    cart = (await client.get("/api/cart", headers=cart_headers(token))).json()
    stale = next(item for item in cart["items"] if item["product_id"] == product["id"])
    assert (
        stale["is_available"] is False and stale["availability_reason"] == "UNAVAILABLE"
    )
    assert len(cart["items"]) == 1
    assert (
        await client.patch(
            f"/api/cart/items/{product['id']}",
            headers=cart_headers(token),
            json={"quantity": 1},
        )
    ).status_code == 409


@pytest.mark.asyncio
async def test_cart_ownership_is_customer_scoped_and_farmer_and_anonymous_are_rejected(
    auth_test_context,
):
    client = auth_test_context["client"]
    token_a, _ = await register(client, "CUSTOMER")
    token_b, _ = await register(client, "CUSTOMER")
    farmer_token, _ = await register(client, "FARMER")
    _, _, _, product = await create_public_product(
        auth_test_context, name=f"Two Carts {uuid4().hex[:6]}", quantity="9"
    )
    assert (await add_item(client, token_b, product["id"], 2)).status_code == 200
    assert (await client.get("/api/cart", headers=cart_headers(token_a))).json()[
        "items"
    ] == []
    assert (
        await client.patch(
            f"/api/cart/items/{product['id']}",
            headers=cart_headers(token_a),
            json={"quantity": 1},
        )
    ).status_code == 404
    assert (
        await client.delete(
            f"/api/cart/items/{product['id']}", headers=cart_headers(token_a)
        )
    ).status_code == 404
    assert (
        await client.delete("/api/cart", headers=cart_headers(token_a))
    ).status_code == 204
    owner_cart = (await client.get("/api/cart", headers=cart_headers(token_b))).json()
    assert owner_cart["items"][0]["quantity"] == 2

    for method, path, body in (
        ("GET", "/api/cart", None),
        ("POST", "/api/cart/items", {"product_id": product["id"], "quantity": 1}),
        ("PATCH", f"/api/cart/items/{product['id']}", {"quantity": 1}),
        ("DELETE", f"/api/cart/items/{product['id']}", None),
        ("DELETE", "/api/cart", None),
    ):
        assert (
            await client.request(
                method, path, headers=cart_headers(farmer_token), json=body
            )
        ).status_code == 403
        assert (await client.request(method, path, json=body)).status_code == 401


@pytest.mark.asyncio
async def test_product_price_changes_are_reflected_using_current_server_price(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    _, _, _, product = await create_public_product(
        auth_test_context,
        name=f"Price Update {uuid4().hex[:6]}",
        price="3.25",
        quantity="5",
    )
    assert (await add_item(client, token, product["id"], 2)).status_code == 200
    await set_product_fields(
        auth_test_context, UUID(product["id"]), price=Decimal("4.75")
    )
    cart = (await client.get("/api/cart", headers=cart_headers(token))).json()
    assert cart["items"][0]["unit_price"] == "4.75"
    assert cart["items"][0]["line_total"] == "9.50"
    assert cart["subtotal"] == "9.50"
