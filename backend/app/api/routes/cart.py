from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_customer
from app.models.user import User
from app.schemas.cart import CartItemAddRequest, CartItemQuantityRequest, CartResponse
from app.services.cart_service import (
    CartCustomerNotFound,
    CartItemNotFound,
    CartProductNotFound,
    CartProductUnavailable,
    CartService,
    CartStockExceeded,
)

router = APIRouter(prefix="/cart", tags=["Cart"])


def _not_found(exc: Exception) -> HTTPException:
    detail = (
        "Customer profile not found"
        if isinstance(exc, CartCustomerNotFound)
        else "Cart item or product not found"
    )
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Product is not currently available for purchase",
    )


def _stock_conflict() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Requested quantity exceeds current available stock",
    )


@router.get(
    "",
    response_model=CartResponse,
    summary="Get the authenticated customer's cart",
    description="Lazily creates an empty customer cart. Prices, line totals, subtotal, item count, and product availability are calculated from current database values. Unavailable items remain visible and inventory is not reserved.",
)
async def get_cart(
    user: User = Depends(require_customer), session: AsyncSession = Depends(get_db)
) -> CartResponse:
    try:
        return await CartService(session).get_cart(user.id)
    except CartCustomerNotFound as exc:
        raise _not_found(exc) from None


@router.post(
    "/items",
    response_model=CartResponse,
    summary="Add a product to the authenticated customer's cart",
    description="Adds the requested quantity or increases the existing line. Quantity must be positive and the resulting quantity must not exceed current stock. Client price and stock fields are rejected.",
)
async def add_cart_item(
    request: CartItemAddRequest,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> CartResponse:
    try:
        return await CartService(session).add_item(
            user.id, request.product_id, request.quantity
        )
    except (CartCustomerNotFound, CartProductNotFound) as exc:
        raise _not_found(exc) from None
    except CartProductUnavailable:
        raise _unavailable() from None
    except CartStockExceeded:
        raise _stock_conflict() from None


@router.patch(
    "/items/{product_id}",
    response_model=CartResponse,
    summary="Change a product quantity in the authenticated customer's cart",
    description="Sets an existing cart item's quantity. The product must remain purchasable and quantity must not exceed its current stock.",
)
async def update_cart_item(
    product_id: UUID,
    request: CartItemQuantityRequest,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> CartResponse:
    try:
        return await CartService(session).update_item(
            user.id, product_id, request.quantity
        )
    except (CartCustomerNotFound, CartItemNotFound, CartProductNotFound) as exc:
        raise _not_found(exc) from None
    except CartProductUnavailable:
        raise _unavailable() from None
    except CartStockExceeded:
        raise _stock_conflict() from None


@router.delete(
    "/items/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Remove a product from the authenticated customer's cart",
)
async def remove_cart_item(
    product_id: UUID,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await CartService(session).remove_item(user.id, product_id)
    except (CartCustomerNotFound, CartItemNotFound) as exc:
        raise _not_found(exc) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Clear the authenticated customer's cart",
    description="Removes all cart items while preserving the customer's cart and all products and inventory.",
)
async def clear_cart(
    user: User = Depends(require_customer), session: AsyncSession = Depends(get_db)
) -> Response:
    try:
        await CartService(session).clear(user.id)
    except CartCustomerNotFound as exc:
        raise _not_found(exc) from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
