from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, order: Order) -> None:
        self.session.add(order)

    async def list_for_customer(
        self, customer_id: UUID, *, page: int, page_size: int
    ) -> tuple[list[Order], int]:
        total = (
            await self.session.scalar(
                select(func.count(Order.id)).where(Order.customer_id == customer_id)
            )
            or 0
        )
        statement = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list((await self.session.scalars(statement)).all()), total

    async def get_for_customer(self, order_id: UUID, customer_id: UUID) -> Order | None:
        statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id, Order.customer_id == customer_id)
        )
        return await self.session.scalar(statement)
