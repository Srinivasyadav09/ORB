from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.models.customer import Customer


class AddressRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_customer(
        self, user_id: UUID, *, for_update: bool = False
    ) -> Customer | None:
        statement = select(Customer).where(Customer.user_id == user_id)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def list_for_customer(self, customer_id: UUID) -> list[Address]:
        statement = (
            select(Address)
            .where(Address.customer_id == customer_id)
            .order_by(Address.created_at, Address.id)
        )
        return list((await self.session.scalars(statement)).all())

    async def get_for_customer(
        self, address_id: UUID, customer_id: UUID, *, for_update: bool = False
    ) -> Address | None:
        statement = select(Address).where(
            Address.id == address_id, Address.customer_id == customer_id
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def get_default(self, customer_id: UUID) -> Address | None:
        statement = select(Address).where(
            Address.customer_id == customer_id, Address.is_default.is_(True)
        )
        return await self.session.scalar(statement)

    async def clear_default(self, customer_id: UUID) -> None:
        await self.session.execute(
            update(Address)
            .where(Address.customer_id == customer_id, Address.is_default.is_(True))
            .values(is_default=False)
        )

    def add(self, address: Address) -> None:
        self.session.add(address)
