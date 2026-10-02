from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.category import CategoryResponse
from app.services.category_service import CategoryNotFound, CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List active marketplace categories",
)
async def list_categories(
    session: AsyncSession = Depends(get_db),
) -> list[CategoryResponse]:
    return await CategoryService(session).list_categories()


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get an active marketplace category",
)
async def get_category(
    category_id: UUID, session: AsyncSession = Depends(get_db)
) -> CategoryResponse:
    try:
        return await CategoryService(session).get_category(category_id)
    except CategoryNotFound:
        raise HTTPException(status_code=404, detail="Category not found") from None
