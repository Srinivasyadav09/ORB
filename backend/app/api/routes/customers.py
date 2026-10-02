from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_customer
from app.models.user import User
from app.schemas.customer import CustomerResponse, CustomerUpdateRequest
from app.services.customer_service import (
    CustomerProfileNotFound,
    CustomerService,
    DuplicatePhoneError,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get(
    "/me",
    response_model=CustomerResponse,
    summary="Get the authenticated customer's profile",
)
async def get_my_profile(
    user: User = Depends(require_customer), session: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    try:
        return await CustomerService(session).get_current_customer(user.id)
    except CustomerProfileNotFound:
        raise HTTPException(
            status_code=404, detail="Customer profile not found"
        ) from None


@router.patch(
    "/me",
    response_model=CustomerResponse,
    summary="Update the authenticated customer's profile",
)
async def update_my_profile(
    request: CustomerUpdateRequest,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    try:
        return await CustomerService(session).update_current_customer(user.id, request)
    except CustomerProfileNotFound:
        raise HTTPException(
            status_code=404, detail="Customer profile not found"
        ) from None
    except DuplicatePhoneError:
        raise HTTPException(
            status_code=409, detail="Phone number is already registered"
        ) from None
