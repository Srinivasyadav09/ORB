from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.farmer import Farmer
from app.models.product import Product


class CartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_customer(
        self, customer_id: UUID, *, for_update: bool = False
    ) -> Cart | None:
        statement = select(Cart).where(Cart.customer_id == customer_id)
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    @staticmethod
    def _item_statement():
        return (
            select(CartItem)
            .join(Product, CartItem.product_id == Product.id)
            .options(
                selectinload(CartItem.product).selectinload(Product.category),
                selectinload(CartItem.product)
                .selectinload(Product.farmer)
                .selectinload(Farmer.user),
            )
        )

    async def list_items(self, cart_id: UUID) -> list[CartItem]:
        statement = (
            self._item_statement()
            .where(CartItem.cart_id == cart_id)
            .order_by(CartItem.created_at, CartItem.id)
        )
        return list((await self.session.scalars(statement)).all())

    async def get_item(
        self, cart_id: UUID, product_id: UUID, *, for_update: bool = False
    ) -> CartItem | None:
        statement = self._item_statement().where(
            CartItem.cart_id == cart_id, CartItem.product_id == product_id
        )
        if for_update:
            statement = statement.with_for_update(of=CartItem)
        return await self.session.scalar(statement)

    async def clear_items(self, cart_id: UUID) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
