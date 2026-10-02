from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import (
    Order,
    OrderStatus,
    PaymentStatus,
)
from app.models.order_item import OrderItem
from app.repositories.address_repository import AddressRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import (
    DeliveryAddressSnapshot,
    OrderCreateRequest,
    OrderItemResponse,
    OrderListItem,
    OrderListResponse,
    OrderResponse,
)
from app.services.order_pricing import calculate_order_totals


class OrderCustomerNotFound(Exception):
    pass


class OrderCartEmpty(Exception):
    pass


class OrderAddressNotFound(Exception):
    pass


class OrderNotFound(Exception):
    pass


class OrderProductUnavailable(Exception):
    pass


class OrderStockExceeded(Exception):
    pass


class OrderNumberConflict(Exception):
    pass


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.customers = CustomerRepository(session)
        self.carts = CartRepository(session)
        self.addresses = AddressRepository(session)
        self.products = ProductRepository(session)
        self.orders = OrderRepository(session)

    async def checkout(
        self, user_id: UUID, request: OrderCreateRequest
    ) -> OrderResponse:
        customer = await self.customers.get_by_user_id(user_id, for_update=True)
        if customer is None:
            raise OrderCustomerNotFound
        cart = await self.carts.get_for_customer(customer.id, for_update=True)
        if cart is None:
            raise OrderCartEmpty
        cart_items = await self.carts.list_items(cart.id)
        if not cart_items:
            raise OrderCartEmpty

        # Lock products in UUID order to keep concurrent multi-item checkouts deadlock-safe.
        products = await self.products.get_many_for_checkout(
            [item.product_id for item in cart_items]
        )
        products_by_id = {product.id: product for product in products}
        for item in cart_items:
            product = products_by_id.get(item.product_id)
            if product is None:
                raise OrderProductUnavailable
            available, _ = self.products.cart_availability(product)
            if not available:
                raise OrderProductUnavailable
            if Decimal(item.quantity) > product.available_quantity:
                raise OrderStockExceeded

        address = await self.addresses.get_for_customer(
            request.address_id, customer.id, for_update=True
        )
        if address is None:
            raise OrderAddressNotFound

        number = f"ORB-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:10].upper()}"
        subtotal = sum(
            (
                products_by_id[item.product_id].price * item.quantity
                for item in cart_items
            ),
            Decimal("0.00"),
        )
        subtotal, delivery_fee, total_amount = calculate_order_totals(subtotal)
        order = Order(
            customer_id=customer.id,
            order_number=number,
            status=OrderStatus.CONFIRMED,
            payment_method=request.payment_method,
            payment_status=PaymentStatus.PENDING,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            currency="INR",
            delivery_full_name=address.full_name,
            delivery_phone=address.phone,
            delivery_address_line_1=address.address_line_1,
            delivery_address_line_2=address.address_line_2,
            delivery_city=address.city,
            delivery_state=address.state,
            delivery_postal_code=address.postal_code,
            delivery_country=address.country,
            delivery_latitude=address.latitude,
            delivery_longitude=address.longitude,
        )
        order_items = []
        for cart_item in cart_items:
            product = products_by_id[cart_item.product_id]
            line_total = product.price * cart_item.quantity
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    farmer_id=product.farmer_id,
                    product_name=product.name,
                    product_image_url=product.image_url,
                    unit=product.unit.value,
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                    line_total=line_total,
                )
            )
            product.available_quantity -= Decimal(cart_item.quantity)
        order.items = order_items
        self.orders.add(order)
        await self.carts.clear_items(cart.id)
        cart.updated_at = datetime.now(timezone.utc)

        try:
            await self.session.flush()
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            constraint = getattr(
                getattr(exc.orig, "diag", None), "constraint_name", None
            )
            if constraint == "uq_orders_order_number":
                raise OrderNumberConflict from exc
            raise

        saved = await self.orders.get_for_customer(order.id, customer.id)
        assert saved is not None
        return self._detail_response(saved)

    async def list_orders(
        self, user_id: UUID, *, page: int, page_size: int
    ) -> OrderListResponse:
        customer = await self.customers.get_by_user_id(user_id)
        if customer is None:
            raise OrderCustomerNotFound
        orders, total = await self.orders.list_for_customer(
            customer.id, page=page, page_size=page_size
        )
        return OrderListResponse(
            items=[self._list_item(order) for order in orders],
            page=page,
            page_size=page_size,
            total=total,
            pages=ceil(total / page_size) if total else 0,
        )

    async def get_order(self, user_id: UUID, order_id: UUID) -> OrderResponse:
        customer = await self.customers.get_by_user_id(user_id)
        if customer is None:
            raise OrderCustomerNotFound
        order = await self.orders.get_for_customer(order_id, customer.id)
        if order is None:
            raise OrderNotFound
        return self._detail_response(order)

    @staticmethod
    def _list_item(order: Order) -> OrderListItem:
        return OrderListItem(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            payment_method=order.payment_method,
            payment_status=order.payment_status,
            subtotal=order.subtotal,
            delivery_fee=order.delivery_fee,
            total_amount=order.total_amount,
            currency=order.currency,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    @classmethod
    def _detail_response(cls, order: Order) -> OrderResponse:
        return OrderResponse(
            **cls._list_item(order).model_dump(),
            delivery_address=DeliveryAddressSnapshot(
                full_name=order.delivery_full_name,
                phone=order.delivery_phone,
                address_line_1=order.delivery_address_line_1,
                address_line_2=order.delivery_address_line_2,
                city=order.delivery_city,
                state=order.delivery_state,
                postal_code=order.delivery_postal_code,
                country=order.delivery_country,
                latitude=order.delivery_latitude,
                longitude=order.delivery_longitude,
            ),
            items=[
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    farmer_id=item.farmer_id,
                    product_name=item.product_name,
                    product_image_url=item.product_image_url,
                    unit=item.unit,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                )
                for item in order.items
            ],
        )
