from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_customer
from app.models.user import User
from app.schemas.address import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
)
from app.services.address_service import (
    AddressCustomerNotFound,
    AddressNotFound,
    AddressService,
)

router = APIRouter(prefix="/addresses", tags=["Addresses"])


def _service(session: AsyncSession) -> AddressService:
    return AddressService(session)


def _handle_missing(exc: Exception) -> HTTPException:
    if isinstance(exc, AddressCustomerNotFound):
        return HTTPException(status_code=404, detail="Customer profile not found")
    return HTTPException(status_code=404, detail="Address not found")


@router.get(
    "",
    response_model=list[AddressResponse],
    summary="List the authenticated customer's saved addresses",
    description="Returns only addresses owned by the authenticated customer. Coordinates are returned only when supplied during address creation or update.",
)
async def list_addresses(
    user: User = Depends(require_customer), session: AsyncSession = Depends(get_db)
) -> list[AddressResponse]:
    try:
        return await _service(session).list_addresses(user.id)
    except AddressCustomerNotFound as exc:
        raise _handle_missing(exc) from None


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a saved delivery address",
    description="Creates an address for the authenticated customer. Latitude and longitude are optional client-supplied coordinates and must be sent together.",
)
async def create_address(
    request: AddressCreateRequest,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> AddressResponse:
    try:
        return await _service(session).create_address(user.id, request)
    except AddressCustomerNotFound as exc:
        raise _handle_missing(exc) from None


@router.get(
    "/default",
    response_model=AddressResponse,
    summary="Get the authenticated customer's default address",
)
async def get_default_address(
    user: User = Depends(require_customer), session: AsyncSession = Depends(get_db)
) -> AddressResponse:
    try:
        return await _service(session).get_default_address(user.id)
    except (AddressCustomerNotFound, AddressNotFound) as exc:
        raise _handle_missing(exc) from None


@router.get(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Get one of the authenticated customer's addresses",
    description="An address owned by another customer is reported as not found.",
)
async def get_address(
    address_id: UUID,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> AddressResponse:
    try:
        return await _service(session).get_address(user.id, address_id)
    except (AddressCustomerNotFound, AddressNotFound) as exc:
        raise _handle_missing(exc) from None


@router.patch(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Update one of the authenticated customer's addresses",
    description="PATCH fields are optional; omitted fields remain unchanged. Ownership and customer identifiers are controlled by the authenticated session.",
)
async def update_address(
    address_id: UUID,
    request: AddressUpdateRequest,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> AddressResponse:
    try:
        return await _service(session).update_address(user.id, address_id, request)
    except (AddressCustomerNotFound, AddressNotFound) as exc:
        raise _handle_missing(exc) from None


@router.patch(
    "/{address_id}/default",
    response_model=AddressResponse,
    summary="Set one of the authenticated customer's addresses as default",
    description="Clears the previous default and selects this owned address. At most one default address is enforced in the database.",
)
async def set_default_address(
    address_id: UUID,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> AddressResponse:
    try:
        return await _service(session).set_default(user.id, address_id)
    except (AddressCustomerNotFound, AddressNotFound) as exc:
        raise _handle_missing(exc) from None


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete one of the authenticated customer's addresses",
    description="Deleting the default address promotes the oldest remaining address; if none remain, no default is selected.",
)
async def delete_address(
    address_id: UUID,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await _service(session).delete_address(user.id, address_id)
    except (AddressCustomerNotFound, AddressNotFound) as exc:
        raise _handle_missing(exc) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
