from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest
from sqlalchemy import select, update

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole
from tests.conftest import fresh_identity


async def register_customer(client, *, email=None, phone=None, password="FreshPass123"):
    generated_email, generated_phone = fresh_identity()
    response = await client.post(
        "/api/auth/register/customer",
        json={
            "full_name": "  Test Customer  ",
            "email": email or generated_email,
            "phone": phone or generated_phone,
            "password": password,
        },
    )
    return response


async def register_farmer(client, *, email=None, phone=None, password="FreshPass123"):
    generated_email, generated_phone = fresh_identity()
    response = await client.post(
        "/api/auth/register/farmer",
        json={
            "full_name": "Test Farmer",
            "email": email or generated_email,
            "phone": phone or generated_phone,
            "password": password,
            "farm_name": "Green Acres",
            "farm_location": "Hyderabad",
            "farm_description": "A small local farm",
            "farm_image_url": "https://example.test/farm.jpg",
            "role": "ADMIN",
            "verification_status": "COMPLETED",
        },
    )
    return response


@pytest.mark.asyncio
async def test_customer_registration_normalizes_email_and_returns_safe_user(
    auth_test_context,
):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    response = await register_customer(client, email=f"  {email.upper()} ", phone=phone)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == email
    assert body["phone"] == phone
    assert body["role"] == "CUSTOMER"
    assert body["customer_profile"]["full_name"] == "Test Customer"
    assert "password" not in body and "password_hash" not in body


@pytest.mark.asyncio
async def test_farmer_registration_creates_submitted_profile_and_ignores_role_fields(
    auth_test_context,
):
    response = await register_farmer(auth_test_context["client"])
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["role"] == "FARMER"
    assert body["farmer_profile"]["verification_status"] == "SUBMITTED"
    assert body["farmer_profile"]["farm_name"] == "Green Acres"
    assert body["farmer_profile"]["verification_submitted_at"]
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_duplicate_email_is_rejected_case_insensitively(auth_test_context):
    client = auth_test_context["client"]
    email, _ = fresh_identity()
    first = await register_customer(client, email=email)
    second = await register_customer(client, email=email.upper())
    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_duplicate_phone_is_rejected_after_normalization(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    first = await register_customer(client, email=email, phone=phone)
    second_email, _ = fresh_identity()
    formatted = f"({phone[1:3]}) {phone[3:8]}-{phone[8:]}"
    second = await register_customer(client, email=second_email, phone=formatted)
    assert first.status_code == 201
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_password_is_argon2_hashed_and_never_returned(auth_test_context):
    context = auth_test_context
    client, factory = context["client"], context["session_factory"]
    password = "FreshPass123"
    response = await register_customer(client, password=password)
    assert response.status_code == 201
    assert password not in response.text
    async with factory() as session:
        user = await session.scalar(
            select(User).where(User.id == UUID(response.json()["id"]))
        )
        assert user is not None
        assert user.password_hash != password
        assert user.password_hash.startswith("$argon2")
        assert verify_password(password, user.password_hash)


@pytest.mark.asyncio
async def test_customer_login_returns_access_and_refresh_tokens(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    assert (
        await register_customer(client, email=email, phone=phone)
    ).status_code == 201
    response = await client.post(
        "/api/auth/login", json={"email": email.upper(), "password": "FreshPass123"}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert body["user"]["role"] == "CUSTOMER"
    assert body["access_token"] and body["refresh_token"]
    assert "password_hash" not in response.text and "FreshPass123" not in response.text


@pytest.mark.asyncio
async def test_farmer_login_succeeds(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    assert (await register_farmer(client, email=email, phone=phone)).status_code == 201
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": "FreshPass123"}
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "FARMER"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email,password",
    [("known", "wrong-password"), ("unknown@example.com", "FreshPass123")],
)
async def test_invalid_credentials_are_generic_401(auth_test_context, email, password):
    client = auth_test_context["client"]
    known_email, known_phone = fresh_identity()
    await register_customer(client, email=known_email, phone=known_phone)
    attempted_email = known_email if email == "known" else email
    response = await client.post(
        "/api/auth/login", json={"email": attempted_email, "password": password}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


@pytest.mark.asyncio
async def test_access_token_and_me_return_database_user(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    tokens = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == email
    assert response.json()["role"] == "CUSTOMER"
    assert "password_hash" not in response.text


@pytest.mark.asyncio
async def test_missing_authorization_returns_401(auth_test_context):
    response = await auth_test_context["client"].get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401(auth_test_context):
    response = await auth_test_context["client"].get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_access_token_returns_401(auth_test_context):
    token = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=1),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    response = await auth_test_context["client"].get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    response = await client.post(
        "/api/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert response.status_code == 200, response.text
    assert response.json()["refresh_token"] == login["refresh_token"]
    me = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {response.json()['access_token']}"},
    )
    assert me.status_code == 200


@pytest.mark.asyncio
async def test_access_token_cannot_be_used_for_refresh(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    response = await client.post(
        "/api/auth/refresh", json={"refresh_token": login["access_token"]}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {login['refresh_token']}"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_cannot_login_or_use_existing_access_token(
    auth_test_context,
):
    context = auth_test_context
    client, factory = context["client"], context["session_factory"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    async with factory() as session, session.begin():
        await session.execute(
            update(User).where(User.email == email).values(is_active=False)
        )
    assert (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).status_code == 401
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rejects_inactive_user(auth_test_context):
    context = auth_test_context
    client, factory = context["client"], context["session_factory"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    async with factory() as session, session.begin():
        await session.execute(
            update(User).where(User.email == email).values(is_active=False)
        )
    response = await client.post(
        "/api/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert response.status_code == 401


async def issue_admin_user(context) -> tuple[str, str]:
    client, factory = context["client"], context["session_factory"]
    email, phone = fresh_identity()
    async with factory() as session, session.begin():
        session.add(
            User(
                email=email,
                phone=phone,
                password_hash=hash_password("FreshPass123"),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
        )
    login = await client.post(
        "/api/auth/login", json={"email": email, "password": "FreshPass123"}
    )
    assert login.status_code == 200
    return email, login.json()["access_token"]


@pytest.mark.asyncio
async def test_role_dependencies_allow_customer_farmer_and_admin(auth_test_context):
    context = auth_test_context
    client = context["client"]
    tokens = []
    for registration, expected_role, endpoint in (
        (register_customer, "CUSTOMER", "customer"),
        (register_farmer, "FARMER", "farmer"),
    ):
        email, phone = fresh_identity()
        assert (await registration(client, email=email, phone=phone)).status_code == 201
        login = (
            await client.post(
                "/api/auth/login", json={"email": email, "password": "FreshPass123"}
            )
        ).json()
        response = await client.get(
            f"/__test__/roles/{endpoint}",
            headers={"Authorization": f"Bearer {login['access_token']}"},
        )
        assert response.status_code == 200 and response.json()["role"] == expected_role
        tokens.append(login["access_token"])
    _, admin_token = await issue_admin_user(context)
    response = await client.get(
        "/__test__/roles/admin", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200 and response.json()["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_customer_cannot_access_farmer_dependency(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    response = await client.get(
        "/__test__/roles/farmer",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_farmer_cannot_access_admin_dependency(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    await register_farmer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    response = await client.get(
        "/__test__/roles/admin",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_logout_explains_stateless_client_side_removal(auth_test_context):
    client = auth_test_context["client"]
    email, phone = fresh_identity()
    await register_customer(client, email=email, phone=phone)
    login = (
        await client.post(
            "/api/auth/login", json={"email": email, "password": "FreshPass123"}
        )
    ).json()
    response = await client.post(
        "/api/auth/logout", headers={"Authorization": f"Bearer {login['access_token']}"}
    )
    assert response.status_code == 200
    assert "Remove stored tokens" in response.json()["message"]


@pytest.mark.asyncio
async def test_expired_refresh_token_returns_401(auth_test_context):
    expired_token = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "type": "refresh",
            "iat": datetime.now(timezone.utc) - timedelta(days=2),
            "exp": datetime.now(timezone.utc) - timedelta(days=1),
        },
        settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    response = await auth_test_context["client"].post(
        "/api/auth/refresh", json={"refresh_token": expired_token}
    )
    assert response.status_code == 401
