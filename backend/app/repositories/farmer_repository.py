from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.farmer import Farmer, VerificationStatus


class FarmerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(
        self, user_id: UUID, *, for_update: bool = False
    ) -> Farmer | None:
        statement = (
            select(Farmer)
            .options(selectinload(Farmer.user))
            .where(Farmer.user_id == user_id)
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def get_by_id(
        self, farmer_id: UUID, *, for_update: bool = False
    ) -> Farmer | None:
        statement = (
            select(Farmer)
            .options(selectinload(Farmer.user))
            .where(Farmer.id == farmer_id)
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def list(
        self, *, page: int, page_size: int, status_filter: VerificationStatus | None
    ):
        filters = (
            []
            if status_filter is None
            else [Farmer.verification_status == status_filter]
        )
        total = (
            await self.session.scalar(select(func.count(Farmer.id)).where(*filters))
            or 0
        )
        statement = (
            select(Farmer)
            .options(selectinload(Farmer.user))
            .where(*filters)
            .order_by(Farmer.verification_submitted_at.desc(), Farmer.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list((await self.session.scalars(statement)).all()), total
