from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, VerificationStatus
from app.repositories.farmer_repository import FarmerRepository
from app.schemas.farmer import FarmerResponse, FarmerUpdateRequest, PublicFarmerResponse


class FarmerProfileNotFound(Exception):
    pass


class DuplicatePhoneError(Exception):
    pass


class FarmerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.farmers = FarmerRepository(session)

    async def get_current_farmer(self, user_id: UUID) -> FarmerResponse:
        farmer = await self.farmers.get_by_user_id(user_id)
        if farmer is None:
            raise FarmerProfileNotFound
        return self._response(farmer)

    async def update_current_farmer(
        self, user_id: UUID, request: FarmerUpdateRequest
    ) -> FarmerResponse:
        farmer = await self.farmers.get_by_user_id(user_id)
        if farmer is None:
            raise FarmerProfileNotFound
        values = request.model_dump(exclude_unset=True)
        for field in (
            "full_name",
            "farm_name",
            "farm_location",
            "farm_description",
            "farm_image_url",
        ):
            if field in values:
                setattr(farmer, field, values[field])
        if "phone" in values:
            farmer.user.phone = values["phone"]
        try:
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(farmer)
            await self.session.refresh(farmer.user)
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicatePhoneError from exc
        return self._response(farmer)

    async def get_public_farmer(self, farmer_id: UUID) -> PublicFarmerResponse:
        farmer = await self.farmers.get_by_id(farmer_id)
        if farmer is None:
            raise FarmerProfileNotFound
        return PublicFarmerResponse(
            id=farmer.id,
            full_name=farmer.full_name,
            farm_name=farmer.farm_name,
            farm_location=farmer.farm_location,
            farm_description=farmer.farm_description,
            farm_image_url=farmer.farm_image_url,
            is_verified=farmer.verification_status == VerificationStatus.COMPLETED,
        )

    @staticmethod
    def _response(farmer: Farmer) -> FarmerResponse:
        return FarmerResponse(
            id=farmer.id,
            full_name=farmer.full_name,
            email=farmer.user.email,
            phone=farmer.user.phone,
            farm_name=farmer.farm_name,
            farm_location=farmer.farm_location,
            farm_description=farmer.farm_description,
            farm_image_url=farmer.farm_image_url,
            verification_status=farmer.verification_status,
            verification_submitted_at=farmer.verification_submitted_at,
            verification_completed_at=farmer.verification_completed_at,
            created_at=farmer.created_at,
            updated_at=farmer.updated_at,
        )
