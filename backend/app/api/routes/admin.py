from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_admin
from app.models.farmer import VerificationStatus
from app.models.user import User
from app.schemas.farmer import AdminFarmerListResponse, AdminFarmerResponse
from app.schemas.verification import (
    FarmerVerificationUpdateRequest,
    VerificationUpdatedResponse,
)
from app.services.verification_service import (
    InvalidVerificationTransition,
    VerificationFarmerNotFound,
    VerificationService,
)

router = APIRouter(prefix="/admin/farmers", tags=["Admin / Farmer Verification"])


@router.get(
    "",
    response_model=AdminFarmerListResponse,
    summary="List farmer verification applications",
)
async def list_farmers(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[VerificationStatus | None, Query(alias="status")] = None,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminFarmerListResponse:
    return await VerificationService(session).list_farmers(
        page=page, page_size=page_size, status_filter=status_filter
    )


@router.get(
    "/{farmer_id}",
    response_model=AdminFarmerResponse,
    summary="Get a farmer verification application",
)
async def get_farmer(
    farmer_id: UUID,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> AdminFarmerResponse:
    try:
        return await VerificationService(session).get_farmer(farmer_id)
    except VerificationFarmerNotFound:
        raise HTTPException(status_code=404, detail="Farmer not found") from None


@router.patch(
    "/{farmer_id}/verification",
    response_model=VerificationUpdatedResponse,
    summary="Advance a farmer verification application",
)
async def update_verification(
    farmer_id: UUID,
    request: FarmerVerificationUpdateRequest,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> VerificationUpdatedResponse:
    try:
        return await VerificationService(session).update_status(
            farmer_id, request.status
        )
    except VerificationFarmerNotFound:
        raise HTTPException(status_code=404, detail="Farmer not found") from None
    except InvalidVerificationTransition:
        raise HTTPException(
            status_code=409, detail="Verification status transition is not allowed"
        ) from None
