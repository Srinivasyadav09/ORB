import asyncio
import re
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from tests.test_addresses import create_address
from tests.test_products import create_public_product
from tests.test_profiles import bearer, register


async def create_customer(context):
    token, user = await register(context["client"], "CUSTOMER")
    address = await create_address(
        context["client"],
        token,
        is_default=True,
        latitude="17.000000",
        longitude="78.000000",
    )
    return token, user, address


async def set_product(context, product_id, **values):
    async with context["session_factory"]() as session:
        product = await session.scalar(select(Product).where(Product.id == product_id))
        assert product is not None
        for field, value in values.items():
            setattr(product, field, value)
        await session.commit()


async def get_product(context, product_id):
    async with context["session_factory"]() as session:
        return await session.scalar(select(Product).where(Product.id == product_id))


async def order_count(context, user_id):
    async with context["session_factory"]() as session:
        customer = await session.scalar(
            select(Customer).where(Customer.user_id == UUID(user_id))
        )
        assert customer is not None
        return len(
            list(
                (
                    await session.scalars(
                        select(Order).where(Order.customer_id == customer.id)
                    )
                ).all()
            )
        )


async def add_to_cart(client, token, product_id, quantity):
    response = await client.post(
        "/api/cart/items",
        headers=bearer(token),
        json={"product_id": str(product_id), "quantity": quantity},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def checkout(client, token, address_id, **extra):
    return await client.post(
        "/api/orders",
        headers=bearer(token),
        json={"address_id": str(address_id), **extra},
    )


@pytest.mark.asyncio
async def test_customer_checkout_snapshots_multiple_items_totals_stock_and_clears_cart(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, user, address = await create_customer(auth_test_context)
    _, farmer_id, _, tomato = await create_public_product(
        auth_test_context,
        name=f"Order Tomatoes {uuid4().hex[:6]}",
        price="12.50",
        quantity="10",
    )
    _, _, _, potato = await create_public_product(
        auth_test_context,
        name=f"Order Potatoes {uuid4().hex[:6]}",
        price="20.00",
        quantity="5",
    )
    await add_to_cart(client, token, tomato["id"], 2)
    await add_to_cart(client, token, potato["id"], 3)
    cart = (
        await client.get("/api/cart", headers=bearer(token))
    ).json()
    assert cart["subtotal"] == "85.00"
    assert cart["delivery_fee"] == "0.00"
    assert cart["total_amount"] == "85.00"

    response = await checkout(client, token, address["id"])
    assert response.status_code == 201, response.text
    order = response.json()
    assert re.fullmatch(r"ORB-\d{8}-[A-F0-9]{10}", order["order_number"])
    assert order["status"] == "CONFIRMED"
    assert order["payment_method"] == "COD" and order["payment_status"] == "PENDING"
    assert order["subtotal"] == "85.00"
    assert order["delivery_fee"] == "0.00" and order["total_amount"] == "85.00"
    assert order["subtotal"] == cart["subtotal"]
    assert order["delivery_fee"] == cart["delivery_fee"]
    assert order["total_amount"] == cart["total_amount"]
    assert Decimal(order["total_amount"]) == (
        Decimal(order["subtotal"]) + Decimal(order["delivery_fee"])
    )
    assert order["currency"] == "INR"
    assert order["delivery_address"]["full_name"] == address["full_name"]
    assert order["delivery_address"]["city"] == address["city"]
    assert order["delivery_address"]["latitude"] == "17.000000"
    assert len(order["items"]) == 2
    tomato_item = next(
        item for item in order["items"] if item["product_id"] == tomato["id"]
    )
    assert tomato_item["farmer_id"] == farmer_id
    assert tomato_item["product_name"] == tomato["name"]
    assert tomato_item["quantity"] == 2
    assert tomato_item["unit_price"] == "12.50"
    assert tomato_item["line_total"] == "25.00"
    assert (
        await get_product(auth_test_context, UUID(tomato["id"]))
    ).available_quantity == Decimal("8.000")
    assert (
        await get_product(auth_test_context, UUID(potato["id"]))
    ).available_quantity == Decimal("2.000")
    assert (await client.get("/api/cart", headers=bearer(token))).json()["items"] == []
    listing = await client.get("/api/orders", headers=bearer(token))
    assert listing.status_code == 200 and listing.json()["total"] == 1
    assert listing.json()["items"][0]["order_number"] == order["order_number"]
    detail = await client.get(f"/api/orders/{order['id']}", headers=bearer(token))
    assert detail.status_code == 200 and detail.json()["items"] == order["items"]
    assert user["id"]
    assert await order_count(auth_test_context, user["id"]) == 1


@pytest.mark.asyncio
async def test_checkout_rejects_empty_cart_and_unowned_or_missing_address_without_mutations(
    auth_test_context,
):
    client = auth_test_context["client"]
    token_a, user_a, address_a = await create_customer(auth_test_context)
    token_b, _, address_b = await create_customer(auth_test_context)
    _, _, _, product = await create_public_product(
        auth_test_context, name=f"Address Check {uuid4().hex[:6]}", quantity="5"
    )
    assert (await checkout(client, token_a, address_a["id"])).status_code == 409
    await add_to_cart(client, token_a, product["id"], 2)
    before = (
        await get_product(auth_test_context, UUID(product["id"]))
    ).available_quantity
    assert (await checkout(client, token_a, address_b["id"])).status_code == 404
    assert (await checkout(client, token_a, uuid4())).status_code == 404
    assert await order_count(auth_test_context, user_a["id"]) == 0
    assert (await client.get("/api/cart", headers=bearer(token_a))).json()["items"][0][
        "quantity"
    ] == 2
    assert (
        await get_product(auth_test_context, UUID(product["id"]))
    ).available_quantity == before
    assert (
        await client.get(
            "/api/addresses/{0}".format(address_a["id"]), headers=bearer(token_a)
        )
    ).status_code == 200


@pytest.mark.asyncio
async def test_order_snapshots_survive_saved_address_and_product_changes(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _, address = await create_customer(auth_test_context)
    _, _, _, product = await create_public_product(
        auth_test_context,
        name=f"Original Name {uuid4().hex[:6]}",
        price="31.25",
        quantity="4",
    )
    await add_to_cart(client, token, product["id"], 2)
    created = await checkout(client, token, address["id"])
    assert created.status_code == 201, created.text
    order = created.json()

    address_change = await client.patch(
        f"/api/addresses/{address['id']}",
        headers=bearer(token),
        json={"city": "Changed City"},
    )
    assert address_change.status_code == 200
    await set_product(
        auth_test_context,
        UUID(product["id"]),
        name="Renamed Product",
        price=Decimal("50.00"),
    )
    detail = await client.get(f"/api/orders/{order['id']}", headers=bearer(token))
    assert detail.status_code == 200
    assert detail.json()["delivery_address"]["city"] == address["city"]
    assert detail.json()["items"][0]["product_name"] == product["name"]
    assert detail.json()["items"][0]["unit_price"] == "31.25"
    assert detail.json()["items"][0]["line_total"] == "62.50"
    assert detail.json()["subtotal"] == "62.50"


@pytest.mark.asyncio
async def test_checkout_failure_preserves_order_stock_and_cart(auth_test_context):
    client = auth_test_context["client"]
    token, user, address = await create_customer(auth_test_context)
    _, _, _, product = await create_public_product(
        auth_test_context, name=f"Insufficient Stock {uuid4().hex[:6]}", quantity="5"
    )
    await add_to_cart(client, token, product["id"], 4)
    await set_product(
        auth_test_context, UUID(product["id"]), available_quantity=Decimal("2")
    )
    response = await checkout(client, token, address["id"])
    assert response.status_code == 409
    assert await order_count(auth_test_context, user["id"]) == 0
    assert (
        await get_product(auth_test_context, UUID(product["id"]))
    ).available_quantity == Decimal("2.000")
    cart = (await client.get("/api/cart", headers=bearer(token))).json()
    assert cart["items"][0]["quantity"] == 4


@pytest.mark.asyncio
async def test_order_rejects_client_owned_totals_and_order_number(auth_test_context):
    client = auth_test_context["client"]
    token, _, address = await create_customer(auth_test_context)
    for extra in (
        {"subtotal": "0.01"},
        {"total_amount": "0.01"},
        {"delivery_fee": "0.00"},
        {"customer_id": str(uuid4())},
        {"order_number": "FAKE-ORDER"},
        {"status": "CANCELLED"},
        {"payment_status": "PAID"},
    ):
        response = await checkout(client, token, address["id"], **extra)
        assert response.status_code == 422
    missing = await client.post("/api/orders", headers=bearer(token), json={})
    assert missing.status_code == 422


@pytest.mark.asyncio
async def test_order_numbers_are_server_generated_unique_and_customer_scoped(
    auth_test_context,
):
    client = auth_test_context["client"]
    token_a, user_a, address_a = await create_customer(auth_test_context)
    token_b, _, address_b = await create_customer(auth_test_context)
    _, _, _, product_a = await create_public_product(
        auth_test_context, name=f"First Order {uuid4().hex[:6]}", quantity="5"
    )
    _, _, _, product_b = await create_public_product(
        auth_test_context, name=f"Second Order {uuid4().hex[:6]}", quantity="5"
    )
    await add_to_cart(client, token_a, product_a["id"], 1)
    order_a = await checkout(client, token_a, address_a["id"])
    await add_to_cart(client, token_b, product_b["id"], 1)
    order_b = await checkout(client, token_b, address_b["id"])
    assert order_a.status_code == order_b.status_code == 201
    assert order_a.json()["order_number"] != order_b.json()["order_number"]
    assert (
        await client.get(f"/api/orders/{order_b.json()['id']}", headers=bearer(token_a))
    ).status_code == 404
    assert (await client.get("/api/orders", headers=bearer(token_a))).json()[
        "total"
    ] == 1
    assert await order_count(auth_test_context, user_a["id"]) == 1
    assert (
        await client.patch(
            f"/api/orders/{order_b.json()['id']}",
            headers=bearer(token_a),
            json={"status": "CANCELLED"},
        )
    ).status_code == 405


@pytest.mark.asyncio
async def test_orders_are_customer_only_and_authentication_is_required(
    auth_test_context,
):
    client = auth_test_context["client"]
    customer_token, _, address = await create_customer(auth_test_context)
    farmer_token, _ = await register(client, "FARMER")
    _, _, _, product = await create_public_product(
        auth_test_context, name=f"Role Check {uuid4().hex[:6]}", quantity="3"
    )
    await add_to_cart(client, customer_token, product["id"], 1)
    created = await checkout(client, customer_token, address["id"])
    assert created.status_code == 201
    for method, path, body in (
        ("GET", "/api/orders", None),
        ("POST", "/api/orders", {"address_id": address["id"]}),
        ("GET", f"/api/orders/{created.json()['id']}", None),
    ):
        assert (
            await client.request(method, path, headers=bearer(farmer_token), json=body)
        ).status_code == 403
        assert (await client.request(method, path, json=body)).status_code == 401


@pytest.mark.asyncio
async def test_concurrent_checkouts_cannot_oversell_stock(auth_test_context):
    client = auth_test_context["client"]
    token_a, _, address_a = await create_customer(auth_test_context)
    token_b, _, address_b = await create_customer(auth_test_context)
    _, _, _, product = await create_public_product(
        auth_test_context, name=f"Concurrent Stock {uuid4().hex[:6]}", quantity="5"
    )
    await add_to_cart(client, token_a, product["id"], 4)
    await add_to_cart(client, token_b, product["id"], 3)

    results = await asyncio.gather(
        checkout(client, token_a, address_a["id"]),
        checkout(client, token_b, address_b["id"]),
    )
    assert sorted(response.status_code for response in results) == [201, 409]
    saved_product = await get_product(auth_test_context, UUID(product["id"]))
    assert saved_product.available_quantity >= 0
    succeeded = next(
        response.json() for response in results if response.status_code == 201
    )
    purchased = sum(item["quantity"] for item in succeeded["items"])
    assert saved_product.available_quantity + purchased == Decimal("5.000")
