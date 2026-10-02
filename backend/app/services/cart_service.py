from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.customer import Customer
from app.models.product import Product
from app.repositories.cart_repository import CartRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import CartItemResponse, CartResponse
from app.services.order_pricing import calculate_order_totals


class CartCustomerNotFound(Exception):
    pass


class CartProductNotFound(Exception):
    pass


class CartProductUnavailable(Exception):
    pass


class CartStockExceeded(Exception):
    pass


class CartItemNotFound(Exception):
    pass


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.customers = CustomerRepository(session)
        self.carts = CartRepository(session)
        self.products = ProductRepository(session)

    async def _lock_customer_and_get_cart(
        self, user_id: UUID
    ) -> tuple[Customer, Cart, bool]:
        customer = await self.customers.get_by_user_id(user_id, for_update=True)
        if customer is None:
            raise CartCustomerNotFound
        cart = await self.carts.get_for_customer(customer.id, for_update=True)
        created = cart is None
        if cart is None:
            cart = Cart(customer_id=customer.id)
            self.session.add(cart)
            await self.session.flush()
        return customer, cart, created

    async def get_cart(self, user_id: UUID) -> CartResponse:
        _, cart, created = await self._lock_customer_and_get_cart(user_id)
        if created:
            await self.session.commit()
            await self.session.refresh(cart)
        return await self._response(cart)

    async def add_item(
        self, user_id: UUID, product_id: UUID, quantity: int
    ) -> CartResponse:
        _, cart, _ = await self._lock_customer_and_get_cart(user_id)
        product = await self.products.get_for_customer_cart(product_id, for_update=True)
        if product is None:
            raise CartProductNotFound
        self._ensure_product_available(product)
        item = await self.carts.get_item(cart.id, product_id, for_update=True)
        target_quantity = quantity + item.quantity if item is not None else quantity
        self._ensure_stock(product, target_quantity)
        if item is None:
            item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
            self.session.add(item)
        else:
            item.quantity = target_quantity
        cart.updated_at = func.now()
        await self.session.flush()
        await self.session.commit()
        saved_cart = await self.carts.get_for_customer(cart.customer_id)
        assert saved_cart is not None
        return await self._response(saved_cart)

    async def update_item(
        self, user_id: UUID, product_id: UUID, quantity: int
    ) -> CartResponse:
        _, cart, _ = await self._lock_customer_and_get_cart(user_id)
        item = await self.carts.get_item(cart.id, product_id, for_update=True)
        if item is None:
            raise CartItemNotFound
        product = await self.products.get_for_customer_cart(product_id, for_update=True)
        if product is None:
            raise CartProductNotFound
        self._ensure_product_available(product)
        self._ensure_stock(product, quantity)
        item.quantity = quantity
        cart.updated_at = func.now()
        await self.session.flush()
        await self.session.commit()
        saved_cart = await self.carts.get_for_customer(cart.customer_id)
        assert saved_cart is not None
        return await self._response(saved_cart)

    async def remove_item(self, user_id: UUID, product_id: UUID) -> None:
        _, cart, _ = await self._lock_customer_and_get_cart(user_id)
        item = await self.carts.get_item(cart.id, product_id, for_update=True)
        if item is None:
            raise CartItemNotFound
        await self.session.delete(item)
        cart.updated_at = func.now()
        await self.session.commit()

    async def clear(self, user_id: UUID) -> None:
        _, cart, _ = await self._lock_customer_and_get_cart(user_id)
        await self.carts.clear_items(cart.id)
        cart.updated_at = func.now()
        await self.session.commit()

    @staticmethod
    def _ensure_product_available(product: Product) -> None:
        available, _ = ProductRepository.cart_availability(product)
        if not available:
            raise CartProductUnavailable

    @staticmethod
    def _ensure_stock(product: Product, quantity: int) -> None:
        if Decimal(quantity) > product.available_quantity:
            raise CartStockExceeded

    async def _response(self, cart: Cart) -> CartResponse:
        items = await self.carts.list_items(cart.id)
        response_items = [self._item_response(item) for item in items]
        subtotal = sum(
            (item.line_total for item in response_items), Decimal("0.00")
        )
        subtotal, delivery_fee, total_amount = calculate_order_totals(subtotal)
        return CartResponse(
            id=cart.id,
            items=response_items,
            item_count=sum(item.quantity for item in response_items),
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
            created_at=cart.created_at,
            updated_at=cart.updated_at,
        )

    @staticmethod
    def _item_response(item: CartItem) -> CartItemResponse:
        product = item.product
        available, reason = ProductRepository.cart_availability(product)
        return CartItemResponse(
            id=item.id,
            product_id=product.id,
            product_name=product.name,
            product_image_url=product.image_url,
            unit=product.unit.value,
            unit_price=product.price,
            quantity=item.quantity,
            available_stock=product.available_quantity,
            line_total=product.price * item.quantity,
            is_available=available,
            availability_reason=reason,
        )
