from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer


class CustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(
        self, user_id: UUID, *, for_update: bool = False
    ) -> Customer | None:
        statement = (
            select(Customer)
            .options(selectinload(Customer.user))
            .where(Customer.user_id == user_id)
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)
