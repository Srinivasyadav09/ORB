import os
from collections.abc import AsyncIterator
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.dependencies import (
    get_current_user,
    require_admin,
    require_customer,
    require_farmer,
)
from app.db.base import Base
from app.main import app
from app.models.user import User

_role_test_router = APIRouter(prefix="/__test__/roles")


@_role_test_router.get("/any")
async def any_role(user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"role": user.role.value}


@_role_test_router.get("/customer")
async def customer_only(user: User = Depends(require_customer)) -> dict[str, str]:
    return {"role": user.role.value}


@_role_test_router.get("/farmer")
async def farmer_only(user: User = Depends(require_farmer)) -> dict[str, str]:
    return {"role": user.role.value}


@_role_test_router.get("/admin")
async def admin_only(user: User = Depends(require_admin)) -> dict[str, str]:
    return {"role": user.role.value}


app.include_router(_role_test_router)


@pytest_asyncio.fixture
async def auth_test_context() -> AsyncIterator[dict]:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail(
            "Backend integration tests require TEST_DATABASE_URL pointing at a dedicated test database"
        )

    engine = create_async_engine(database_url, pool_pre_ping=True)
    async with engine.begin() as connection:
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield {"client": client, "session_factory": factory}
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


def fresh_identity() -> tuple[str, str]:
    suffix = uuid4().hex
    return (
        f"user-{suffix}@example.com",
        f"+91{int(suffix[:10], 16) % 10_000_000_000:010d}",
    )
