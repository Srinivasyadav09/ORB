from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.customer_profile), selectinload(User.farmer_profile)
            )
            .where(User.email == email)
        )
        return await self.session.scalar(statement)

    async def get_by_id(self, user_id: UUID) -> User | None:
        statement = (
            select(User)
            .options(
                selectinload(User.customer_profile), selectinload(User.farmer_profile)
            )
            .where(User.id == user_id)
        )
        return await self.session.scalar(statement)

    async def email_exists(self, email: str) -> bool:
        return (
            await self.session.scalar(select(User.id).where(User.email == email))
            is not None
        )

    async def phone_exists(self, phone: str) -> bool:
        return (
            await self.session.scalar(select(User.id).where(User.phone == phone))
            is not None
        )

    def add(self, user: User) -> None:
        self.session.add(user)
