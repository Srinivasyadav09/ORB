from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_farmer
from app.models.user import User
from app.schemas.farmer import FarmerResponse, FarmerUpdateRequest, PublicFarmerResponse
from app.schemas.verification import FarmerVerificationResponse
from app.services.farmer_service import (
    DuplicatePhoneError,
    FarmerProfileNotFound,
    FarmerService,
)
from app.services.verification_service import (
    VerificationFarmerNotFound,
    VerificationService,
)

router = APIRouter(prefix="/farmers", tags=["Farmers"])


@router.get(
    "/me",
    response_model=FarmerResponse,
    summary="Get the authenticated farmer's profile",
)
async def get_my_profile(
    user: User = Depends(require_farmer), session: AsyncSession = Depends(get_db)
) -> FarmerResponse:
    try:
        return await FarmerService(session).get_current_farmer(user.id)
    except FarmerProfileNotFound:
        raise HTTPException(
            status_code=404, detail="Farmer profile not found"
        ) from None


@router.patch(
    "/me",
    response_model=FarmerResponse,
    summary="Update the authenticated farmer's profile",
)
async def update_my_profile(
    request: FarmerUpdateRequest,
    user: User = Depends(require_farmer),
    session: AsyncSession = Depends(get_db),
) -> FarmerResponse:
    try:
        return await FarmerService(session).update_current_farmer(user.id, request)
    except FarmerProfileNotFound:
        raise HTTPException(
            status_code=404, detail="Farmer profile not found"
        ) from None
    except DuplicatePhoneError:
        raise HTTPException(
            status_code=409, detail="Phone number is already registered"
        ) from None


@router.get(
    "/me/verification",
    response_model=FarmerVerificationResponse,
    summary="Get own verification status",
)
async def get_my_verification(
    user: User = Depends(require_farmer), session: AsyncSession = Depends(get_db)
) -> FarmerVerificationResponse:
    try:
        return await VerificationService(session).get_status(user.id)
    except VerificationFarmerNotFound:
        raise HTTPException(
            status_code=404, detail="Farmer profile not found"
        ) from None


@router.get(
    "/{farmer_id}",
    response_model=PublicFarmerResponse,
    summary="Get a public farmer profile",
)
async def get_public_profile(
    farmer_id: UUID, session: AsyncSession = Depends(get_db)
) -> PublicFarmerResponse:
    try:
        return await FarmerService(session).get_public_farmer(farmer_id)
    except FarmerProfileNotFound:
        raise HTTPException(status_code=404, detail="Farmer not found") from None
