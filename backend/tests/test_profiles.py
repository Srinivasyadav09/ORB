from uuid import UUID

import pytest

from app.core.security import hash_password
from app.models.user import User, UserRole
from tests.conftest import fresh_identity


async def register(client, role: str):
    email, phone = fresh_identity()
    endpoint = "customer" if role == "CUSTOMER" else "farmer"
    data = {
        "full_name": "Sample Farmer" if role == "FARMER" else "Sample Customer",
        "email": email,
        "phone": phone,
        "password": "FreshPass123",
    }
    if role == "FARMER":
        data.update(
            {
                "farm_name": "Green Acres",
                "farm_location": "Hyderabad",
                "farm_description": "Fresh produce",
            }
        )
    response = await client.post(f"/api/auth/register/{endpoint}", json=data)
    assert response.status_code == 201, response.text
    login = await client.post(
        "/api/auth/login", json={"email": email, "password": "FreshPass123"}
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"], login.json()["user"]


async def make_admin(context):
    email, phone = fresh_identity()
    async with context["session_factory"]() as session, session.begin():
        session.add(
            User(
                email=email,
                phone=phone,
                password_hash=hash_password("FreshPass123"),
                role=UserRole.ADMIN,
            )
        )
    login = await context["client"].post(
        "/api/auth/login", json={"email": email, "password": "FreshPass123"}
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_customer_profile_read_and_update_are_scoped_and_safe(auth_test_context):
    client = auth_test_context["client"]
    token, user = await register(client, "CUSTOMER")
    response = await client.get("/api/customers/me", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["full_name"] == "Sample Customer"
    assert response.json()["email"] == user["email"]
    assert "password_hash" not in response.text and "role" not in response.json()
    replacement_phone = fresh_identity()[1]
    update = await client.patch(
        "/api/customers/me",
        headers=bearer(token),
        json={
            "full_name": "  Updated Customer ",
            "phone": replacement_phone,
            "profile_image_url": "https://example.test/customer.png",
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["full_name"] == "Updated Customer"
    assert update.json()["phone"] == replacement_phone
    assert update.json()["profile_image_url"] == "https://example.test/customer.png"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"role": "ADMIN"},
        {"is_verified": True},
        {"is_active": False},
        {"user_id": "00000000-0000-0000-0000-000000000001"},
        {"password_hash": "unsafe"},
        {"created_at": "2026-01-01T00:00:00Z"},
        {"updated_at": "2026-01-01T00:00:00Z"},
        {"verification_status": "COMPLETED"},
    ],
)
async def test_customer_cannot_update_protected_fields(auth_test_context, payload):
    token, _ = await register(auth_test_context["client"], "CUSTOMER")
    response = await auth_test_context["client"].patch(
        "/api/customers/me", headers=bearer(token), json=payload
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_customer_profile_role_auth_and_phone_conflict(auth_test_context):
    client = auth_test_context["client"]
    first_token, _ = await register(client, "CUSTOMER")
    second_token, _ = await register(client, "CUSTOMER")
    other_profile = (
        await client.get("/api/customers/me", headers=bearer(second_token))
    ).json()
    conflict = await client.patch(
        "/api/customers/me",
        headers=bearer(first_token),
        json={"phone": other_profile["phone"]},
    )
    assert conflict.status_code == 409
    assert (await client.get("/api/customers/me")).status_code == 401
    farmer_token, _ = await register(client, "FARMER")
    admin_token = await make_admin(auth_test_context)
    assert (
        await client.get("/api/customers/me", headers=bearer(farmer_token))
    ).status_code == 403
    assert (
        await client.get("/api/customers/me", headers=bearer(admin_token))
    ).status_code == 403


@pytest.mark.asyncio
async def test_farmer_profile_read_update_and_forbidden_verification_edits(
    auth_test_context,
):
    client = auth_test_context["client"]
    token, user = await register(client, "FARMER")
    replacement_phone = fresh_identity()[1]
    response = await client.get("/api/farmers/me", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["verification_status"] == "SUBMITTED"
    assert response.json()["email"] == user["email"]
    update = await client.patch(
        "/api/farmers/me",
        headers=bearer(token),
        json={
            "full_name": " Updated Farmer ",
            "farm_name": "New Farm",
            "phone": replacement_phone,
            "farm_location": "Warangal, Telangana",
            "farm_description": " Local seasonal produce ",
            "farm_image_url": "https://example.test/farm.png",
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["full_name"] == "Updated Farmer"
    assert update.json()["farm_location"] == "Warangal, Telangana"
    assert update.json()["verification_status"] == "SUBMITTED"
    for payload in (
        {"verification_status": "COMPLETED"},
        {"verification_submitted_at": "2026-01-01T00:00:00Z"},
        {"verification_completed_at": "2026-01-01T00:00:00Z"},
        {"role": "ADMIN"},
        {"is_verified": True},
    ):
        forbidden = await client.patch(
            "/api/farmers/me", headers=bearer(token), json=payload
        )
        assert forbidden.status_code == 422
    assert (await client.get("/api/farmers/me")).status_code == 401
    customer_token, _ = await register(client, "CUSTOMER")
    assert (
        await client.get("/api/farmers/me", headers=bearer(customer_token))
    ).status_code == 403


@pytest.mark.asyncio
async def test_public_farmer_profile_is_safe_and_unknown_id_is_404(auth_test_context):
    client = auth_test_context["client"]
    token, user = await register(client, "FARMER")
    own = (await client.get("/api/farmers/me", headers=bearer(token))).json()
    response = await client.get(f"/api/farmers/{own['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Sample Farmer"
    assert body["is_verified"] is False
    assert (
        "email" not in body
        and "phone" not in body
        and "verification_submitted_at" not in body
    )
    assert "password_hash" not in response.text and user["email"] not in response.text
    missing = await client.get("/api/farmers/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_farmer_verification_workflow_and_timestamp_transitions(
    auth_test_context,
):
    client = auth_test_context["client"]
    farmer_token, _ = await register(client, "FARMER")
    admin_token = await make_admin(auth_test_context)
    profile = (await client.get("/api/farmers/me", headers=bearer(farmer_token))).json()
    farmer_id = profile["id"]
    initial = await client.get(
        "/api/farmers/me/verification", headers=bearer(farmer_token)
    )
    assert initial.status_code == 200
    submitted_at = initial.json()["submitted_at"]
    assert (
        initial.json()["status"] == "SUBMITTED"
        and initial.json()["completed_at"] is None
    )
    assert (await client.get("/api/farmers/me/verification")).status_code == 401
    assert (
        await client.get("/api/farmers/me/verification", headers=bearer(admin_token))
    ).status_code == 403
    assert (
        await client.patch(
            f"/api/admin/farmers/{farmer_id}/verification",
            headers=bearer(farmer_token),
            json={"status": "COMPLETED"},
        )
    ).status_code == 403

    listing = await client.get(
        "/api/admin/farmers?page=1&page_size=1&status=SUBMITTED",
        headers=bearer(admin_token),
    )
    assert listing.status_code == 200, listing.text
    assert listing.json()["page_size"] == 1 and listing.json()["total"] >= 1
    assert len(listing.json()["items"]) == 1
    detail = await client.get(
        f"/api/admin/farmers/{farmer_id}", headers=bearer(admin_token)
    )
    assert detail.status_code == 200 and detail.json()["email"]
    assert "password_hash" not in detail.text and "access_token" not in detail.text

    moved = await client.patch(
        f"/api/admin/farmers/{farmer_id}/verification",
        headers=bearer(admin_token),
        json={"status": "VERIFYING"},
    )
    assert moved.status_code == 200, moved.text
    assert (
        moved.json()["status"] == "VERIFYING" and moved.json()["completed_at"] is None
    )
    completed = await client.patch(
        f"/api/admin/farmers/{farmer_id}/verification",
        headers=bearer(admin_token),
        json={"status": "COMPLETED"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["completed_at"] is not None
    invalid = await client.patch(
        f"/api/admin/farmers/{farmer_id}/verification",
        headers=bearer(admin_token),
        json={"status": "SUBMITTED"},
    )
    assert invalid.status_code == 409
    still_completed = await client.get(
        "/api/farmers/me/verification", headers=bearer(farmer_token)
    )
    assert still_completed.json()["status"] == "COMPLETED"
    assert still_completed.json()["submitted_at"] == submitted_at
    assert (
        await client.patch(
            "/api/farmers/me",
            headers=bearer(farmer_token),
            json={"verification_status": "COMPLETED"},
        )
    ).status_code == 422


@pytest.mark.asyncio
async def test_verification_rejection_and_admin_resubmission_reset_timestamps(
    auth_test_context,
):
    client = auth_test_context["client"]
    farmer_token, _ = await register(client, "FARMER")
    admin_token = await make_admin(auth_test_context)
    farmer = (await client.get("/api/farmers/me", headers=bearer(farmer_token))).json()
    farmer_id = UUID(farmer["id"])
    rejected = await client.patch(
        f"/api/admin/farmers/{farmer_id}/verification",
        headers=bearer(admin_token),
        json={"status": "REJECTED"},
    )
    assert rejected.status_code == 200
    assert (
        rejected.json()["status"] == "REJECTED"
        and rejected.json()["completed_at"] is None
    )
    resubmitted = await client.patch(
        f"/api/admin/farmers/{farmer_id}/verification",
        headers=bearer(admin_token),
        json={"status": "SUBMITTED"},
    )
    assert resubmitted.status_code == 200
    assert resubmitted.json()["status"] == "SUBMITTED"
    assert resubmitted.json()["submitted_at"] >= farmer["verification_submitted_at"]
    assert resubmitted.json()["completed_at"] is None


@pytest.mark.asyncio
async def test_admin_list_pagination_validation_and_non_admin_access(auth_test_context):
    client = auth_test_context["client"]
    admin_token = await make_admin(auth_test_context)
    customer_token, _ = await register(client, "CUSTOMER")
    for query in ("page=0", "page_size=0", "page_size=101"):
        assert (
            await client.get(f"/api/admin/farmers?{query}", headers=bearer(admin_token))
        ).status_code == 422
    assert (
        await client.get("/api/admin/farmers", headers=bearer(customer_token))
    ).status_code == 403
    assert (await client.get("/api/admin/farmers")).status_code == 401
