from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_admin
from app.models.product import ProductStatus
from app.models.user import User
from app.schemas.product import ProductListResponse, ProductResponse
from app.services.product_service import ProductNotFound, ProductService

router = APIRouter(prefix="/admin/products", tags=["Admin / Products"])


@router.get(
    "", response_model=ProductListResponse, summary="List products for moderation"
)
async def list_products(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[ProductStatus | None, Query(alias="status")] = None,
    farmer_id: UUID | None = None,
    category_id: UUID | None = None,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    return await ProductService(session).list_admin_products(
        page=page,
        page_size=page_size,
        status=status_filter,
        farmer_id=farmer_id,
        category_id=category_id,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product for moderation",
)
async def get_product(
    product_id: UUID,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> ProductResponse:
    try:
        return await ProductService(session).get_admin_product(product_id)
    except ProductNotFound:
        raise HTTPException(status_code=404, detail="Product not found") from None
