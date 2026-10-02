from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.product import ProductDetailResponse, ProductListResponse
from app.services.product_service import (
    InvalidProductPriceRange,
    ProductNotFound,
    ProductService,
)

router = APIRouter(prefix="/products", tags=["Products"])
ProductSort = Literal["newest", "oldest", "price_low", "price_high", "name"]


@router.get("", response_model=ProductListResponse, summary="Browse active products")
async def list_products(
    page: Annotated[int, Query(ge=1, description="Page number, starting at 1")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Number of products, maximum 100")
    ] = 20,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    category_id: UUID | None = None,
    category: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
    min_price: Annotated[
        Decimal | None, Query(ge=0, max_digits=12, decimal_places=2)
    ] = None,
    max_price: Annotated[
        Decimal | None, Query(ge=0, max_digits=12, decimal_places=2)
    ] = None,
    available: bool | None = None,
    farmer_id: UUID | None = None,
    sort: ProductSort = "newest",
    session: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    try:
        return await ProductService(session).list_marketplace(
            page=page,
            page_size=page_size,
            search=search.strip() if search else None,
            category_id=category_id,
            category=category.strip() if category else None,
            min_price=min_price,
            max_price=max_price,
            available=available,
            farmer_id=farmer_id,
            sort=sort,
        )
    except InvalidProductPriceRange:
        raise HTTPException(
            status_code=422, detail="min_price must not exceed max_price"
        ) from None


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Get an active product detail",
)
async def get_product(
    product_id: UUID, session: AsyncSession = Depends(get_db)
) -> ProductDetailResponse:
    try:
        return await ProductService(session).get_public_product(product_id)
    except ProductNotFound:
        raise HTTPException(status_code=404, detail="Product not found") from None
