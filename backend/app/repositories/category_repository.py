from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[Category]:
        statement = (
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(func.lower(Category.name))
        )
        return list((await self.session.scalars(statement)).all())

    async def get_active_by_id(self, category_id: UUID) -> Category | None:
        statement = select(Category).where(
            Category.id == category_id, Category.is_active.is_(True)
        )
        return await self.session.scalar(statement)

    async def get_by_name(self, name: str) -> Category | None:
        return await self.session.scalar(
            select(Category).where(func.lower(Category.name) == name.casefold())
        )
