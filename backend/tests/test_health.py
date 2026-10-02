import os

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.config import Settings
from app.core.security import verify_password
from app.main import app


@pytest.mark.asyncio
async def test_root_health() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_api_health() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_database_health_returns_503_when_database_is_unavailable() -> None:
    """The real endpoint must not report success when the DB connection fails."""
    unavailable_engine = create_async_engine(
        "postgresql+asyncpg://orb_user:orb_password@127.0.0.1:1/orb_test",
        connect_args={"timeout": 0.2},
    )
    factory = async_sessionmaker(unavailable_engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/api/health/db")
    finally:
        app.dependency_overrides.clear()
        await unavailable_engine.dispose()

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "disconnected"}


@pytest.mark.asyncio
async def test_database_health_returns_200_when_database_is_available() -> None:
    class HealthySession:
        async def execute(self, _statement):
            return None

    async def override_get_db():
        yield HealthySession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/api/health/db")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_debug_configuration_accepts_boolean_and_legacy_environment_values() -> None:
    for value in (True, "true"):
        assert Settings(DEBUG=value, _env_file=None).DEBUG is True
    for value in (False, "false", "release", "production", "staging"):
        assert Settings(DEBUG=value, _env_file=None).DEBUG is False


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Set TEST_DATABASE_URL to run SELECT 1 against an isolated test DB",
)
async def test_database_health_with_test_database() -> None:
    """Execute the endpoint's real SELECT 1 against TEST_DATABASE_URL only."""
    test_engine = create_async_engine(
        os.environ["TEST_DATABASE_URL"], pool_pre_ping=True
    )
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/api/health/db")
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


@pytest.mark.asyncio
async def test_password_validation_does_not_echo_plaintext_secret() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/register/customer",
            json={
                "email": "safe@example.com",
                "phone": "+919123456789",
                "full_name": "Safe User",
                "password": "secret",
            },
        )
    assert response.status_code == 422
    assert "secret" not in response.text


def test_corrupt_password_hash_is_rejected_without_exception() -> None:
    assert verify_password("anything", "not-a-pwdlib-hash") is False
