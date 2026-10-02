from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.category import Category
from app.models.farmer import Farmer
from app.models.product import Product, ProductStatus, ProductUnit
from tests.test_profiles import bearer, make_admin, register


async def make_category(context, *, name=None, active=True):
    category = Category(name=name or f"Test category {uuid4().hex}", is_active=active)
    async with context["session_factory"]() as session, session.begin():
        session.add(category)
        await session.flush()
        category_id = category.id
    return category_id


async def verify_farmer(context, token):
    client = context["client"]
    profile = (await client.get("/api/farmers/me", headers=bearer(token))).json()
    admin = await make_admin(context)
    for target in ("VERIFYING", "COMPLETED"):
        response = await client.patch(
            f"/api/admin/farmers/{profile['id']}/verification",
            headers=bearer(admin),
            json={"status": target},
        )
        assert response.status_code == 200, response.text
    return profile["id"], admin


async def create_public_product(
    context,
    *,
    name="Golden Tomatoes",
    description="fresh red produce",
    price="42.50",
    quantity="12.500",
    unit="kg",
    category_id=None,
    image_url="https://images.example.test/tomatoes.jpg",
    status="ACTIVE",
):
    client = context["client"]
    token, _ = await register(client, "FARMER")
    farmer_id, admin = await verify_farmer(context, token)
    category_id = category_id or await make_category(context)
    payload = {
        "name": name,
        "description": description,
        "category_id": str(category_id),
        "price": price,
        "unit": unit,
        "available_quantity": quantity,
        "image_url": image_url,
        "status": status,
    }
    response = await client.post(
        "/api/farmers/me/products", headers=bearer(token), json=payload
    )
    assert response.status_code == 201, response.text
    return token, farmer_id, admin, response.json()


@pytest.mark.asyncio
async def test_category_list_detail_and_inactive_category_behavior(auth_test_context):
    client = auth_test_context["client"]
    active_id = await make_category(auth_test_context)
    inactive_id = await make_category(auth_test_context, active=False)
    listing = await client.get("/api/categories")
    assert listing.status_code == 200
    assert any(row["id"] == str(active_id) for row in listing.json())
    assert all(row["id"] != str(inactive_id) for row in listing.json())
    detail = await client.get(f"/api/categories/{active_id}")
    assert detail.status_code == 200 and detail.json()["id"] == str(active_id)
    assert (await client.get(f"/api/categories/{inactive_id}")).status_code == 404
    assert (await client.get(f"/api/categories/{uuid4()}")).status_code == 404


@pytest.mark.asyncio
async def test_farmer_can_create_list_read_update_and_soft_deactivate_product(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, farmer_id, _, product = await create_public_product(auth_test_context)
    assert product["status"] == "ACTIVE"
    assert product["price"] == "42.50"
    assert product["available_quantity"] == "12.500"
    assert product["category"]["id"]
    assert product["farmer"]["id"] == farmer_id
    assert product["is_available"] is True

    listing = await client.get(
        "/api/farmers/me/products?page=1&page_size=10", headers=bearer(token)
    )
    assert listing.status_code == 200
    assert any(row["id"] == product["id"] for row in listing.json()["items"])
    detail = await client.get(
        f"/api/farmers/me/products/{product['id']}", headers=bearer(token)
    )
    assert (
        detail.status_code == 200
        and detail.json()["description"] == "fresh red produce"
    )

    update = await client.patch(
        f"/api/farmers/me/products/{product['id']}",
        headers=bearer(token),
        json={
            "name": "  Ripe Tomatoes ",
            "price": "45.00",
            "available_quantity": "0",
            "image_url": None,
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["name"] == "Ripe Tomatoes"
    assert update.json()["price"] == "45.00"
    assert update.json()["available_quantity"] == "0.000"
    assert update.json()["is_available"] is False
    assert update.json()["status"] == "ACTIVE"

    deleted = await client.delete(
        f"/api/farmers/me/products/{product['id']}", headers=bearer(token)
    )
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "INACTIVE"
    assert (await client.get(f"/api/products/{product['id']}")).status_code == 404
    still_owned = await client.get(
        f"/api/farmers/me/products/{product['id']}", headers=bearer(token)
    )
    assert still_owned.status_code == 200 and still_owned.json()["status"] == "INACTIVE"


@pytest.mark.asyncio
async def test_unverified_farmer_can_create_draft_but_cannot_publish(auth_test_context):
    client = auth_test_context["client"]
    token, _ = await register(client, "FARMER")
    category_id = await make_category(auth_test_context)
    base = {
        "name": "Draft Cucumbers",
        "category_id": str(category_id),
        "price": "30.00",
        "unit": "kg",
        "available_quantity": "8",
    }
    created = await client.post(
        "/api/farmers/me/products", headers=bearer(token), json=base
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "DRAFT"
    active_create = await client.post(
        "/api/farmers/me/products",
        headers=bearer(token),
        json={**base, "name": "Forbidden Active", "status": "ACTIVE"},
    )
    assert active_create.status_code == 403
    publish = await client.patch(
        f"/api/farmers/me/products/{created.json()['id']}",
        headers=bearer(token),
        json={"status": "ACTIVE"},
    )
    assert publish.status_code == 403

    _, admin = await verify_farmer(auth_test_context, token)
    publish = await client.patch(
        f"/api/farmers/me/products/{created.json()['id']}",
        headers=bearer(token),
        json={"status": "ACTIVE"},
    )
    assert publish.status_code == 200 and publish.json()["status"] == "ACTIVE"
    assert admin


@pytest.mark.asyncio
async def test_marketplace_search_filters_sort_and_pagination(auth_test_context):
    client = auth_test_context["client"]
    tag = uuid4().hex[:8]
    category_name = f"Vegetables {tag}"
    category_id = await make_category(auth_test_context, name=category_name)
    farmer_token, farmer_id, _, first = await create_public_product(
        auth_test_context,
        name=f"Ruby Tomato {tag}",
        description=f"Summer red harvest {tag}",
        price="20.00",
        quantity="4",
        category_id=category_id,
    )
    second_response = await client.post(
        "/api/farmers/me/products",
        headers=bearer(farmer_token),
        json={
            "name": f"Green Tomato {tag}",
            "description": f"Firm green harvest {tag}",
            "category_id": str(category_id),
            "price": "50.00",
            "unit": "kg",
            "available_quantity": "0",
            "status": "ACTIVE",
        },
    )
    assert second_response.status_code == 201, second_response.text
    second = second_response.json()
    _, other_farmer_id, _, _ = await create_public_product(
        auth_test_context,
        name=f"Other Farmer Pear {tag}",
        description=f"sweet fruit {tag}",
        price="90.00",
        quantity="3",
    )

    all_products = await client.get("/api/products?page=1&page_size=2")
    assert all_products.status_code == 200
    assert all_products.json()["page"] == 1 and all_products.json()["page_size"] == 2
    assert all_products.json()["pages"] >= 2
    assert len(all_products.json()["items"]) == 2

    search = await client.get("/api/products", params={"search": f"RUBY TOMATO {tag}"})
    assert search.status_code == 200 and [
        x["name"] for x in search.json()["items"]
    ] == [first["name"]]
    description_search = await client.get(
        "/api/products", params={"search": f"summer red harvest {tag}"}
    )
    assert description_search.json()["total"] == 1
    category_search = await client.get(
        "/api/products", params={"category_id": str(category_id)}
    )
    assert category_search.json()["total"] == 2
    category_by_name = await client.get(
        "/api/products", params={"category": category_name}
    )
    assert category_by_name.json()["total"] == 2

    price_filter = await client.get(
        "/api/products", params={"min_price": "25", "max_price": "60", "search": tag}
    )
    assert price_filter.status_code == 200
    assert [item["name"] for item in price_filter.json()["items"]] == [second["name"]]
    assert (
        await client.get("/api/products?min_price=100&max_price=10")
    ).status_code == 422
    assert (await client.get("/api/products?available=true")).json()["total"] >= 1
    unavailable = await client.get("/api/products?available=false")
    assert unavailable.status_code == 200
    assert any(
        item["id"] == second["id"] and item["status"] == "ACTIVE"
        for item in unavailable.json()["items"]
    )
    by_farmer = await client.get(f"/api/products?farmer_id={farmer_id}")
    assert by_farmer.status_code == 200 and by_farmer.json()["total"] == 2
    assert other_farmer_id != farmer_id
    low = await client.get("/api/products?sort=price_low")
    prices = [Decimal(row["price"]) for row in low.json()["items"]]
    assert prices == sorted(prices)
    high = await client.get("/api/products?sort=price_high")
    prices_high = [Decimal(row["price"]) for row in high.json()["items"]]
    assert prices_high == sorted(prices_high, reverse=True)
    names = await client.get("/api/products?sort=name")
    assert [row["name"].casefold() for row in names.json()["items"]] == sorted(
        row["name"].casefold() for row in names.json()["items"]
    )
    assert (await client.get("/api/products?sort=arbitrary_sql")).status_code == 422
    assert (await client.get("/api/products?page=0")).status_code == 422
    assert (await client.get("/api/products?page_size=101")).status_code == 422
    assert (await client.get(f"/api/products/{second['id']}")).json()[
        "is_available"
    ] is False
    assert farmer_token


@pytest.mark.asyncio
async def test_public_detail_hides_draft_inactive_and_unknown_products(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "FARMER")
    category_id = await make_category(auth_test_context)
    draft = await client.post(
        "/api/farmers/me/products",
        headers=bearer(token),
        json={
            "name": "Private Draft",
            "category_id": str(category_id),
            "price": "10",
            "unit": "piece",
        },
    )
    assert draft.status_code == 201
    assert (await client.get(f"/api/products/{draft.json()['id']}")).status_code == 404
    assert (await client.get(f"/api/products/{uuid4()}")).status_code == 404


@pytest.mark.asyncio
async def test_product_update_validation_category_and_protected_fields(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _, _, product = await create_public_product(auth_test_context)
    product_id = product["id"]
    invalid_category = await client.patch(
        f"/api/farmers/me/products/{product_id}",
        headers=bearer(token),
        json={"category_id": str(uuid4())},
    )
    assert invalid_category.status_code == 422
    for body in (
        {"farmer_id": str(uuid4())},
        {"id": str(uuid4())},
        {"created_at": "2026-01-01T00:00:00Z"},
        {"updated_at": "2026-01-01T00:00:00Z"},
        {"price": "0"},
        {"price": "-1"},
        {"available_quantity": "-0.001"},
        {"unit": "bushel"},
        {"status": "PUBLISHED"},
        {"image_url": "data:image/png;base64,AAAA"},
    ):
        result = await client.patch(
            f"/api/farmers/me/products/{product_id}", headers=bearer(token), json=body
        )
        assert result.status_code == 422, (body, result.text)
    illegal_transition = await client.patch(
        f"/api/farmers/me/products/{product_id}",
        headers=bearer(token),
        json={"status": "DRAFT"},
    )
    assert illegal_transition.status_code == 409
    create_inactive = await client.post(
        "/api/farmers/me/products",
        headers=bearer(token),
        json={
            "name": "Invalid initial state",
            "category_id": product["category"]["id"],
            "price": "1",
            "unit": "kg",
            "status": "INACTIVE",
        },
    )
    assert create_inactive.status_code == 422
    create_bad_category = await client.post(
        "/api/farmers/me/products",
        headers=bearer(token),
        json={
            "name": "No category",
            "category_id": str(uuid4()),
            "price": "1",
            "unit": "kg",
        },
    )
    assert create_bad_category.status_code == 422
    assert (
        await client.patch(
            f"/api/farmers/me/products/{product_id}", headers=bearer(token), json={}
        )
    ).status_code == 422


@pytest.mark.asyncio
async def test_farmer_product_ownership_and_role_authorization(auth_test_context):
    client = auth_test_context["client"]
    owner_token, _, _, product = await create_public_product(auth_test_context)
    other_token, _ = await register(client, "FARMER")
    customer_token, _ = await register(client, "CUSTOMER")
    path = f"/api/farmers/me/products/{product['id']}"
    assert (await client.get(path, headers=bearer(other_token))).status_code == 404
    assert (
        await client.patch(path, headers=bearer(other_token), json={"name": "stolen"})
    ).status_code == 404
    assert (await client.delete(path, headers=bearer(other_token))).status_code == 404
    assert (
        await client.get("/api/farmers/me/products", headers=bearer(customer_token))
    ).status_code == 403
    assert (await client.get("/api/farmers/me/products")).status_code == 401
    assert owner_token


@pytest.mark.asyncio
async def test_admin_product_listing_and_moderation_access(auth_test_context):
    client = auth_test_context["client"]
    token, farmer_id, admin_token, product = await create_public_product(
        auth_test_context
    )
    listing = await client.get(
        f"/api/admin/products?status=ACTIVE&farmer_id={farmer_id}&category_id={product['category']['id']}",
        headers=bearer(admin_token),
    )
    assert listing.status_code == 200
    assert any(item["id"] == product["id"] for item in listing.json()["items"])
    detail = await client.get(
        f"/api/admin/products/{product['id']}", headers=bearer(admin_token)
    )
    assert detail.status_code == 200
    customer_token, _ = await register(client, "CUSTOMER")
    assert (
        await client.get("/api/admin/products", headers=bearer(customer_token))
    ).status_code == 403
    assert (await client.get("/api/admin/products")).status_code == 401
    assert token


@pytest.mark.asyncio
async def test_unique_category_name_and_product_foreign_keys(auth_test_context):
    context = auth_test_context
    category_name = f"Unique {uuid4().hex}"
    await make_category(context, name=category_name)
    async with context["session_factory"]() as session:
        session.add(Category(name=category_name.upper()))
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()

    farmer_token, farmer = await register(context["client"], "FARMER")
    async with context["session_factory"]() as session:
        farmer_row = await session.scalar(
            select(Farmer).where(Farmer.user_id == farmer["id"])
        )
        product = Product(
            farmer_id=farmer_row.id,
            category_id=uuid4(),
            name="Broken foreign key",
            price=Decimal("1.00"),
            unit=ProductUnit.KG,
            available_quantity=Decimal("1"),
            status=ProductStatus.DRAFT,
        )
        session.add(product)
        with pytest.raises(IntegrityError):
            await session.flush()
        await session.rollback()
    assert farmer_token


@pytest.mark.asyncio
async def test_inactive_category_hides_its_public_products(auth_test_context):
    client = auth_test_context["client"]
    _, _, _, product = await create_public_product(auth_test_context)
    category_id = product["category"]["id"]
    async with auth_test_context["session_factory"]() as session, session.begin():
        category = await session.get(Category, category_id)
        category.is_active = False
    assert (await client.get(f"/api/products/{product['id']}")).status_code == 404
    listing = await client.get("/api/products", params={"category_id": category_id})
    assert listing.status_code == 200 and listing.json()["total"] == 0
    assert (await client.get(f"/api/categories/{category_id}")).status_code == 404
