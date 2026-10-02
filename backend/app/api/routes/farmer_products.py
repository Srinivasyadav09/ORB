from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_farmer
from app.models.product import ProductStatus
from app.models.user import User
from app.schemas.product import (
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.services.product_service import (
    InvalidProductStatusTransition,
    ProductCategoryNotFound,
    ProductFarmerNotFound,
    ProductNotFound,
    ProductService,
    UnverifiedFarmerCannotPublish,
)

router = APIRouter(prefix="/farmers/me/products", tags=["Products"])
ProductSort = Literal["newest", "oldest", "price_low", "price_high", "name"]


def product_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProductFarmerNotFound):
        return HTTPException(status_code=404, detail="Farmer profile not found")
    if isinstance(exc, ProductNotFound):
        return HTTPException(status_code=404, detail="Product not found")
    if isinstance(exc, ProductCategoryNotFound):
        return HTTPException(status_code=422, detail="Category is unavailable")
    if isinstance(exc, UnverifiedFarmerCannotPublish):
        return HTTPException(
            status_code=403,
            detail="Farmer verification is required to publish products",
        )
    if isinstance(exc, InvalidProductStatusTransition):
        return HTTPException(
            status_code=409, detail="Product status transition is not allowed"
        )
    raise exc


@router.get(
    "",
    response_model=ProductListResponse,
    summary="List the authenticated farmer's products",
)
async def list_my_products(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[ProductStatus | None, Query(alias="status")] = None,
    category_id: UUID | None = None,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    sort: ProductSort = "newest",
    user: User = Depends(require_farmer),
    session: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    try:
        return await ProductService(session).list_farmer_products(
            user.id,
            page=page,
            page_size=page_size,
            status=status_filter,
            category_id=category_id,
            search=search.strip() if search else None,
            sort=sort,
        )
    except (
        ProductFarmerNotFound,
        ProductNotFound,
        ProductCategoryNotFound,
        UnverifiedFarmerCannotPublish,
        InvalidProductStatusTransition,
    ) as exc:
        raise product_error(exc) from None


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
async def create_product(
    request: ProductCreateRequest,
    user: User = Depends(require_farmer),
    session: AsyncSession = Depends(get_db),
) -> ProductResponse:
    try:
        return await ProductService(session).create_farmer_product(user.id, request)
    except (
        ProductFarmerNotFound,
        ProductNotFound,
        ProductCategoryNotFound,
        UnverifiedFarmerCannotPublish,
        InvalidProductStatusTransition,
    ) as exc:
        raise product_error(exc) from None


@router.get(
    "/{product_id}", response_model=ProductResponse, summary="Get an owned product"
)
async def get_my_product(
    product_id: UUID,
    user: User = Depends(require_farmer),
    session: AsyncSession = Depends(get_db),
) -> ProductResponse:
    try:
        return await ProductService(session).get_farmer_product(user.id, product_id)
    except (
        ProductFarmerNotFound,
        ProductNotFound,
        ProductCategoryNotFound,
        UnverifiedFarmerCannotPublish,
        InvalidProductStatusTransition,
    ) as exc:
        raise product_error(exc) from None


@router.patch(
    "/{product_id}", response_model=ProductResponse, summary="Update an owned product"
)
async def update_product(
    product_id: UUID,
    request: ProductUpdateRequest,
    user: User = Depends(require_farmer),
    session: AsyncSession = Depends(get_db),
) -> ProductResponse:
    try:
        return await ProductService(session).update_farmer_product(
            user.id, product_id, request
        )
    except (
        ProductFarmerNotFound,
        ProductNotFound,
        ProductCategoryNotFound,
        UnverifiedFarmerCannotPublish,
        InvalidProductStatusTransition,
    ) as exc:
        raise product_error(exc) from None


@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Deactivate an owned product",
)
async def delete_product(
    product_id: UUID,
    user: User = Depends(require_farmer),
    session: AsyncSession = Depends(get_db),
) -> ProductResponse:
    try:
        return await ProductService(session).deactivate_farmer_product(
            user.id, product_id
        )
    except (
        ProductFarmerNotFound,
        ProductNotFound,
        ProductCategoryNotFound,
        UnverifiedFarmerCannotPublish,
        InvalidProductStatusTransition,
    ) as exc:
        raise product_error(exc) from None
