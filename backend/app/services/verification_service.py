from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, VerificationStatus
from app.repositories.farmer_repository import FarmerRepository
from app.schemas.farmer import AdminFarmerListResponse, AdminFarmerResponse
from app.schemas.verification import (
    FarmerVerificationResponse,
    VerificationUpdatedResponse,
)

STATUS_MESSAGES = {
    VerificationStatus.SUBMITTED: "Your verification request has been submitted and is waiting for review.",
    VerificationStatus.VERIFYING: "Your farm details are being reviewed.",
    VerificationStatus.COMPLETED: "Your farmer profile has been verified.",
    VerificationStatus.REJECTED: "Your verification request was not approved. Contact support for next steps.",
}

# Rejected applications may be resubmitted by an administrator after the farmer
# has corrected their information. Completion is terminal.
ALLOWED_TRANSITIONS = {
    VerificationStatus.SUBMITTED: {
        VerificationStatus.VERIFYING,
        VerificationStatus.REJECTED,
    },
    VerificationStatus.VERIFYING: {
        VerificationStatus.COMPLETED,
        VerificationStatus.REJECTED,
    },
    VerificationStatus.REJECTED: {VerificationStatus.SUBMITTED},
    VerificationStatus.COMPLETED: set(),
}


class VerificationFarmerNotFound(Exception):
    pass


class InvalidVerificationTransition(Exception):
    pass


class VerificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.farmers = FarmerRepository(session)

    async def get_status(self, user_id: UUID) -> FarmerVerificationResponse:
        farmer = await self.farmers.get_by_user_id(user_id)
        if farmer is None:
            raise VerificationFarmerNotFound
        return self._verification_response(farmer)

    async def list_farmers(
        self, *, page: int, page_size: int, status_filter: VerificationStatus | None
    ) -> AdminFarmerListResponse:
        farmers, total = await self.farmers.list(
            page=page, page_size=page_size, status_filter=status_filter
        )
        return AdminFarmerListResponse(
            items=[self._admin_response(farmer) for farmer in farmers],
            page=page,
            page_size=page_size,
            total=total,
            pages=ceil(total / page_size) if total else 0,
        )

    async def get_farmer(self, farmer_id: UUID) -> AdminFarmerResponse:
        farmer = await self.farmers.get_by_id(farmer_id)
        if farmer is None:
            raise VerificationFarmerNotFound
        return self._admin_response(farmer)

    async def update_status(
        self, farmer_id: UUID, new_status: VerificationStatus
    ) -> VerificationUpdatedResponse:
        farmer = await self.farmers.get_by_id(farmer_id, for_update=True)
        if farmer is None:
            raise VerificationFarmerNotFound
        old_status = farmer.verification_status
        if (
            old_status != new_status
            and new_status not in ALLOWED_TRANSITIONS[old_status]
        ):
            raise InvalidVerificationTransition
        if old_status != new_status:
            now = datetime.now(timezone.utc)
            farmer.verification_status = new_status
            if new_status == VerificationStatus.SUBMITTED:
                farmer.verification_submitted_at = now
                farmer.verification_completed_at = None
            elif new_status == VerificationStatus.COMPLETED:
                farmer.verification_completed_at = now
            else:
                farmer.verification_completed_at = None
            await self.session.flush()
            await self.session.commit()
        return VerificationUpdatedResponse(
            farmer_id=farmer.id,
            status=farmer.verification_status,
            submitted_at=farmer.verification_submitted_at,
            completed_at=farmer.verification_completed_at,
            status_message=STATUS_MESSAGES[farmer.verification_status],
        )

    @staticmethod
    def _verification_response(farmer: Farmer) -> FarmerVerificationResponse:
        return FarmerVerificationResponse(
            status=farmer.verification_status,
            submitted_at=farmer.verification_submitted_at,
            completed_at=farmer.verification_completed_at,
            status_message=STATUS_MESSAGES[farmer.verification_status],
        )

    @staticmethod
    def _admin_response(farmer: Farmer) -> AdminFarmerResponse:
        return AdminFarmerResponse(
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
