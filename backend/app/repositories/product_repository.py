from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.farmer import Farmer, VerificationStatus
from app.models.product import Product, ProductStatus
from app.models.user import User


class ProductRepository:
    @staticmethod
    def marketplace_visibility_filters():
        return [
            Product.status == ProductStatus.ACTIVE,
            Farmer.verification_status == VerificationStatus.COMPLETED,
            User.is_active.is_(True),
            Category.is_active.is_(True),
        ]

    @staticmethod
    def cart_availability(product: Product) -> tuple[bool, str | None]:
        if product.status != ProductStatus.ACTIVE:
            return False, "UNAVAILABLE"
        if product.available_quantity <= 0:
            return False, "OUT_OF_STOCK"
        if not product.category.is_active:
            return False, "UNAVAILABLE"
        if product.farmer.verification_status != VerificationStatus.COMPLETED:
            return False, "UNAVAILABLE"
        if not product.farmer.user.is_active:
            return False, "UNAVAILABLE"
        return True, None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _search_filter(search: str | None):
        if not search:
            return None
        escaped = search.replace("/", "//").replace("%", "/%").replace("_", "/_")
        pattern = f"%{escaped}%"
        return or_(
            Product.name.ilike(pattern, escape="/"),
            Product.description.ilike(pattern, escape="/"),
            Category.name.ilike(pattern, escape="/"),
        )

    @staticmethod
    def _category_filter(category_id: UUID | None, category: str | None):
        if category_id is not None:
            return Category.id == category_id
        if category:
            return func.lower(Category.name) == category.casefold()
        return None

    @staticmethod
    def _price_filters(min_price: Decimal | None, max_price: Decimal | None):
        filters = []
        if min_price is not None:
            filters.append(Product.price >= min_price)
        if max_price is not None:
            filters.append(Product.price <= max_price)
        return filters

    @staticmethod
    def _sort(statement, sort: str):
        if sort == "oldest":
            return statement.order_by(Product.created_at.asc(), Product.id)
        if sort == "price_low":
            return statement.order_by(Product.price.asc(), Product.id)
        if sort == "price_high":
            return statement.order_by(Product.price.desc(), Product.id)
        if sort == "name":
            return statement.order_by(func.lower(Product.name), Product.id)
        return statement.order_by(Product.created_at.desc(), Product.id)

    @staticmethod
    def _eager_statement():
        return select(Product).options(
            selectinload(Product.category), selectinload(Product.farmer)
        )

    async def list_marketplace(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        category_id: UUID | None,
        category: str | None,
        min_price: Decimal | None,
        max_price: Decimal | None,
        available: bool | None,
        farmer_id: UUID | None,
        sort: str,
    ) -> tuple[list[Product], int]:
        filters = self.marketplace_visibility_filters()
        category_filter = self._category_filter(category_id, category)
        if category_filter is not None:
            filters.append(category_filter)
        price_filters = self._price_filters(min_price, max_price)
        filters.extend(price_filters)
        if available is True:
            filters.append(Product.available_quantity > 0)
        elif available is False:
            filters.append(Product.available_quantity <= 0)
        if farmer_id is not None:
            filters.append(Product.farmer_id == farmer_id)
        search_filter = self._search_filter(search)
        if search_filter is not None:
            filters.append(search_filter)

        count_statement = (
            select(func.count(Product.id))
            .join(Category, Product.category_id == Category.id)
            .join(Farmer, Product.farmer_id == Farmer.id)
            .join(User, Farmer.user_id == User.id)
            .where(*filters)
        )
        total = await self.session.scalar(count_statement) or 0
        statement = (
            self._eager_statement()
            .join(Category, Product.category_id == Category.id)
            .join(Farmer, Product.farmer_id == Farmer.id)
            .join(User, Farmer.user_id == User.id)
            .where(*filters)
        )
        statement = (
            self._sort(statement, sort).offset((page - 1) * page_size).limit(page_size)
        )
        return list((await self.session.scalars(statement)).all()), total

    async def list_for_farmer(
        self,
        *,
        farmer_id: UUID,
        page: int,
        page_size: int,
        status: ProductStatus | None,
        category_id: UUID | None,
        search: str | None,
        sort: str,
    ) -> tuple[list[Product], int]:
        filters = [Product.farmer_id == farmer_id]
        if status is not None:
            filters.append(Product.status == status)
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        if search:
            escaped = search.replace("/", "//").replace("%", "/%").replace("_", "/_")
            pattern = f"%{escaped}%"
            filters.append(
                or_(
                    Product.name.ilike(pattern, escape="/"),
                    Product.description.ilike(pattern, escape="/"),
                )
            )
        total = (
            await self.session.scalar(select(func.count(Product.id)).where(*filters))
            or 0
        )
        statement = self._eager_statement().where(*filters)
        statement = (
            self._sort(statement, sort).offset((page - 1) * page_size).limit(page_size)
        )
        return list((await self.session.scalars(statement)).all()), total

    async def list_for_admin(
        self,
        *,
        page: int,
        page_size: int,
        status: ProductStatus | None,
        farmer_id: UUID | None,
        category_id: UUID | None,
    ) -> tuple[list[Product], int]:
        filters = []
        if status is not None:
            filters.append(Product.status == status)
        if farmer_id is not None:
            filters.append(Product.farmer_id == farmer_id)
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        total = (
            await self.session.scalar(select(func.count(Product.id)).where(*filters))
            or 0
        )
        statement = self._eager_statement().where(*filters)
        statement = (
            self._sort(statement, "newest")
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list((await self.session.scalars(statement)).all()), total

    async def get_for_farmer(
        self, product_id: UUID, farmer_id: UUID, *, for_update: bool = False
    ) -> Product | None:
        statement = self._eager_statement().where(
            Product.id == product_id, Product.farmer_id == farmer_id
        )
        if for_update:
            statement = statement.with_for_update()
        return await self.session.scalar(statement)

    async def get_public(self, product_id: UUID) -> Product | None:
        statement = (
            self._eager_statement()
            .join(Category, Product.category_id == Category.id)
            .join(Farmer, Product.farmer_id == Farmer.id)
            .join(User, Farmer.user_id == User.id)
            .where(Product.id == product_id, *self.marketplace_visibility_filters())
        )
        return await self.session.scalar(statement)

    async def get_many_for_checkout(self, product_ids: list[UUID]) -> list[Product]:
        if not product_ids:
            return []
        statement = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.farmer).selectinload(Farmer.user),
            )
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update(of=Product)
            .execution_options(populate_existing=True)
        )
        return list((await self.session.scalars(statement)).all())

    async def get_for_customer_cart(
        self, product_id: UUID, *, for_update: bool = False
    ) -> Product | None:
        statement = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.farmer).selectinload(Farmer.user),
            )
            .where(Product.id == product_id)
        )
        if for_update:
            statement = statement.with_for_update(of=Product)
        return await self.session.scalar(statement)

    async def get_for_admin(self, product_id: UUID) -> Product | None:
        statement = self._eager_statement().where(Product.id == product_id)
        return await self.session.scalar(statement)

    def add(self, product: Product) -> None:
        self.session.add(product)
