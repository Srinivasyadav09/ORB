from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import require_customer
from app.models.user import User
from app.schemas.order import OrderCreateRequest, OrderListResponse, OrderResponse
from app.services.order_service import (
    OrderAddressNotFound,
    OrderCartEmpty,
    OrderCustomerNotFound,
    OrderNumberConflict,
    OrderNotFound,
    OrderProductUnavailable,
    OrderService,
    OrderStockExceeded,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _not_found(detail: str = "Order not found") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an order from the authenticated customer's cart",
    description="Requires an owned saved address. Checkout locks and validates current products and stock, calculates current prices server-side, snapshots the delivery address and product details, decrements inventory, and clears the cart atomically. Payment is represented as COD/PENDING; no payment is processed.",
)
async def create_order(
    request: OrderCreateRequest,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> OrderResponse:
    try:
        return await OrderService(session).checkout(user.id, request)
    except (OrderCustomerNotFound, OrderNotFound):
        raise _not_found("Customer cart or profile not found") from None
    except OrderAddressNotFound:
        raise _not_found("Delivery address not found") from None
    except OrderCartEmpty:
        raise HTTPException(
            status_code=409, detail="Cannot create an order from an empty cart"
        ) from None
    except OrderProductUnavailable:
        raise HTTPException(
            status_code=409, detail="A cart product is no longer available"
        ) from None
    except OrderStockExceeded:
        raise HTTPException(
            status_code=409, detail="A cart quantity exceeds current available stock"
        ) from None
    except OrderNumberConflict:
        raise HTTPException(
            status_code=409,
            detail="Could not generate a unique order number; retry checkout",
        ) from None


@router.get(
    "",
    response_model=OrderListResponse,
    summary="List the authenticated customer's orders",
    description="Returns only orders owned by the authenticated customer, newest first.",
)
async def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> OrderListResponse:
    try:
        return await OrderService(session).list_orders(
            user.id, page=page, page_size=page_size
        )
    except OrderCustomerNotFound:
        raise _not_found("Customer profile not found") from None


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get one of the authenticated customer's orders",
    description="Returns price, product, and delivery-address snapshots. Another customer's order is reported as not found.",
)
async def get_order(
    order_id: UUID,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> OrderResponse:
    try:
        return await OrderService(session).get_order(user.id, order_id)
    except (OrderCustomerNotFound, OrderNotFound):
        raise _not_found() from None
