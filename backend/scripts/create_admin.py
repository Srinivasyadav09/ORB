"""Create one admin account using environment identity and an interactive password."""

import asyncio
import getpass
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionFactory, engine
from app.models.user import User, UserRole


async def main() -> None:
    email = os.getenv("ADMIN_EMAIL", "").strip().casefold()
    full_name = os.getenv("ADMIN_FULL_NAME", "").strip()
    phone = os.getenv("ADMIN_PHONE", "").strip() or None
    if not email or not full_name:
        raise SystemExit(
            "Set ADMIN_EMAIL and ADMIN_FULL_NAME before running this script."
        )
    password = getpass.getpass("Admin password (minimum 8 characters): ")
    if len(password) < 8 or not password.strip():
        raise SystemExit("Password must contain at least 8 non-blank characters.")

    try:
        async with AsyncSessionFactory() as session, session.begin():
            existing = await session.scalar(select(User.id).where(User.email == email))
            if existing:
                raise SystemExit("An account with that email already exists.")
            if phone and await session.scalar(
                select(User.id).where(User.phone == phone)
            ):
                raise SystemExit("An account with that phone already exists.")
            session.add(
                User(
                    email=email,
                    phone=phone,
                    password_hash=hash_password(password),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True,
                )
            )
    finally:
        await engine.dispose()
    print(f"Admin account created for {email}.")


if __name__ == "__main__":
    asyncio.run(main())
