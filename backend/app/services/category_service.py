from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryResponse


class CategoryNotFound(Exception):
    pass


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.categories = CategoryRepository(session)

    async def list_categories(self) -> list[CategoryResponse]:
        return [
            CategoryResponse.model_validate(row)
            for row in await self.categories.list_active()
        ]

    async def get_category(self, category_id: UUID) -> CategoryResponse:
        category = await self.categories.get_active_by_id(category_id)
        if category is None:
            raise CategoryNotFound
        return CategoryResponse.model_validate(category)
