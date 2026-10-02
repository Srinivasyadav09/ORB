from uuid import uuid4

import pytest

from tests.test_profiles import bearer, register


def address_payload(**overrides):
    payload = {
        "full_name": "Sample Customer",
        "phone": "+919876543210",
        "address_line_1": "12 Example Road",
        "address_line_2": "Floor 2",
        "city": "Hyderabad",
        "state": "Telangana",
        "postal_code": "500001",
        "country": "India",
        "label": "Home",
        "is_default": False,
    }
    payload.update(overrides)
    return payload


async def create_address(client, token, **overrides):
    response = await client.post(
        "/api/addresses", headers=bearer(token), json=address_payload(**overrides)
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_customer_address_crud_and_patch_preserves_omitted_fields(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    created = await create_address(client, token, is_default=True)
    assert created["full_name"] == "Sample Customer"
    assert created["is_default"] is True
    assert "customer_id" not in created

    listing = await client.get("/api/addresses", headers=bearer(token))
    assert listing.status_code == 200 and [row["id"] for row in listing.json()] == [
        created["id"]
    ]
    detail = await client.get(f"/api/addresses/{created['id']}", headers=bearer(token))
    assert detail.status_code == 200 and detail.json()["id"] == created["id"]

    updated = await client.patch(
        f"/api/addresses/{created['id']}",
        headers=bearer(token),
        json={"city": "  Warangal  "},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["city"] == "Warangal"
    assert updated.json()["address_line_1"] == "12 Example Road"
    assert updated.json()["is_default"] is True

    deleted = await client.delete(
        f"/api/addresses/{created['id']}", headers=bearer(token)
    )
    assert deleted.status_code == 204 and deleted.content == b""
    assert (
        await client.get(f"/api/addresses/{created['id']}", headers=bearer(token))
    ).status_code == 404


@pytest.mark.asyncio
async def test_default_address_replacement_retrieval_and_delete_promotion(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    first = await create_address(client, token, label="First", is_default=True)
    second = await create_address(client, token, label="Second", is_default=True)
    assert (
        await client.get(f"/api/addresses/{first['id']}", headers=bearer(token))
    ).json()["is_default"] is False
    assert (await client.get("/api/addresses/default", headers=bearer(token))).json()[
        "id"
    ] == second["id"]

    third = await create_address(client, token, label="Third")
    selected = await client.patch(
        f"/api/addresses/{third['id']}/default", headers=bearer(token)
    )
    assert selected.status_code == 200 and selected.json()["is_default"] is True
    listing = (await client.get("/api/addresses", headers=bearer(token))).json()
    assert sum(item["is_default"] for item in listing) == 1
    assert (await client.get("/api/addresses/default", headers=bearer(token))).json()[
        "id"
    ] == third["id"]

    # The list order is oldest first; deleting the default promotes that address.
    await client.delete(f"/api/addresses/{third['id']}", headers=bearer(token))
    promoted = await client.get("/api/addresses/default", headers=bearer(token))
    assert promoted.status_code == 200 and promoted.json()["id"] == first["id"]
    await client.delete(f"/api/addresses/{first['id']}", headers=bearer(token))
    await client.delete(f"/api/addresses/{second['id']}", headers=bearer(token))
    assert (
        await client.get("/api/addresses/default", headers=bearer(token))
    ).status_code == 404


@pytest.mark.asyncio
async def test_customer_address_ownership_is_hidden_for_read_update_delete_and_default(
    auth_test_context,
):
    client = auth_test_context["client"]
    token_a, _ = await register(client, "CUSTOMER")
    token_b, _ = await register(client, "CUSTOMER")
    foreign = await create_address(client, token_b, is_default=True)

    assert (
        await client.get(f"/api/addresses/{foreign['id']}", headers=bearer(token_a))
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/addresses/{foreign['id']}",
            headers=bearer(token_a),
            json={"city": "Nope"},
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/addresses/{foreign['id']}", headers=bearer(token_a))
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/addresses/{foreign['id']}/default", headers=bearer(token_a)
        )
    ).status_code == 404
    assert (await client.get("/api/addresses", headers=bearer(token_a))).json() == []
    assert (
        await client.get("/api/addresses/default", headers=bearer(token_a))
    ).status_code == 404


@pytest.mark.asyncio
async def test_address_endpoints_require_customer_role_and_authentication(
    auth_test_context,
):
    client = auth_test_context["client"]
    farmer_token, _ = await register(client, "FARMER")
    customer_token, _ = await register(client, "CUSTOMER")
    created = await create_address(client, customer_token)
    paths = [
        ("get", "/api/addresses", None),
        ("post", "/api/addresses", address_payload()),
        ("get", "/api/addresses/default", None),
        ("get", f"/api/addresses/{created['id']}", None),
        ("patch", f"/api/addresses/{created['id']}", {"city": "X"}),
        ("delete", f"/api/addresses/{created['id']}", None),
        ("patch", f"/api/addresses/{created['id']}/default", None),
    ]
    for method, path, body in paths:
        response = await client.request(
            method.upper(), path, headers=bearer(farmer_token), json=body
        )
        assert response.status_code == 403, (method, path, response.text)
        response = await client.request(method.upper(), path, json=body)
        assert response.status_code == 401, (method, path, response.text)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"latitude": 90.000001, "longitude": 0},
        {"latitude": -90.000001, "longitude": 0},
        {"latitude": 0, "longitude": 180.000001},
        {"latitude": 0, "longitude": -180.000001},
        {"latitude": 12},
        {"longitude": 12},
    ],
)
async def test_invalid_coordinates_are_rejected(auth_test_context, overrides):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    response = await client.post(
        "/api/addresses", headers=bearer(token), json=address_payload(**overrides)
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_coordinates_are_optional_and_valid_decimal_coordinates_are_accepted(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    omitted = await create_address(client, token)
    assert omitted["latitude"] is None and omitted["longitude"] is None
    supplied = await create_address(
        client, token, latitude="17.000000", longitude="78.000000"
    )
    assert supplied["latitude"] == "17.000000"
    assert supplied["longitude"] == "78.000000"


@pytest.mark.asyncio
async def test_address_payload_protects_customer_and_timestamp_fields(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    forbidden_create = await client.post(
        "/api/addresses",
        headers=bearer(token),
        json=address_payload(customer_id=str(uuid4())),
    )
    assert forbidden_create.status_code == 422
    created = await create_address(client, token)
    for protected in (
        {"customer_id": str(uuid4())},
        {"created_at": "2026-01-01T00:00:00Z"},
        {"updated_at": "2026-01-01T00:00:00Z"},
    ):
        response = await client.patch(
            f"/api/addresses/{created['id']}", headers=bearer(token), json=protected
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_nonexistent_address_and_empty_patch_return_validation_errors(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, _ = await register(client, "CUSTOMER")
    missing = uuid4()
    assert (
        await client.get(f"/api/addresses/{missing}", headers=bearer(token))
    ).status_code == 404
    assert (
        await client.patch(
            f"/api/addresses/{missing}", headers=bearer(token), json={"city": "X"}
        )
    ).status_code == 404
    assert (
        await client.delete(f"/api/addresses/{missing}", headers=bearer(token))
    ).status_code == 404
    assert (
        await client.patch(f"/api/addresses/{missing}/default", headers=bearer(token))
    ).status_code == 404
    assert (
        await client.patch(
            "/api/addresses/00000000-0000-0000-0000-000000000001",
            headers=bearer(token),
            json={},
        )
    ).status_code == 422
