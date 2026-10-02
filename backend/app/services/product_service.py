from math import ceil
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farmer import Farmer, VerificationStatus
from app.models.product import Product, ProductStatus
from app.repositories.category_repository import CategoryRepository
from app.repositories.farmer_repository import FarmerRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCategorySummary,
    ProductCreateRequest,
    ProductDetailResponse,
    ProductFarmerSummary,
    ProductListItem,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)

PRODUCT_STATUS_TRANSITIONS = {
    ProductStatus.DRAFT: {ProductStatus.ACTIVE, ProductStatus.INACTIVE},
    ProductStatus.ACTIVE: {ProductStatus.INACTIVE},
    ProductStatus.INACTIVE: {ProductStatus.DRAFT, ProductStatus.ACTIVE},
}


class InvalidProductStatusTransition(Exception):
    pass


class ProductNotFound(Exception):
    pass


class ProductCategoryNotFound(Exception):
    pass


class ProductFarmerNotFound(Exception):
    pass


class UnverifiedFarmerCannotPublish(Exception):
    pass


class InvalidProductPriceRange(Exception):
    pass


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.products = ProductRepository(session)
        self.categories = CategoryRepository(session)
        self.farmers = FarmerRepository(session)

    async def list_marketplace(self, **filters) -> ProductListResponse:
        self._validate_price_range(filters.get("min_price"), filters.get("max_price"))
        products, total = await self.products.list_marketplace(**filters)
        return self._list_response(
            products, total, filters["page"], filters["page_size"]
        )

    async def get_public_product(self, product_id: UUID) -> ProductDetailResponse:
        product = await self.products.get_public(product_id)
        if product is None:
            raise ProductNotFound
        return self._detail_response(product)

    async def list_farmer_products(
        self, user_id: UUID, **filters
    ) -> ProductListResponse:
        farmer = await self.farmers.get_by_user_id(user_id)
        if farmer is None:
            raise ProductFarmerNotFound
        products, total = await self.products.list_for_farmer(
            farmer_id=farmer.id, **filters
        )
        return self._list_response(
            products, total, filters["page"], filters["page_size"]
        )

    async def get_farmer_product(
        self, user_id: UUID, product_id: UUID
    ) -> ProductResponse:
        farmer = await self.farmers.get_by_user_id(user_id)
        if farmer is None:
            raise ProductFarmerNotFound
        product = await self.products.get_for_farmer(product_id, farmer.id)
        if product is None:
            raise ProductNotFound
        return self._detail_response(product)

    async def create_farmer_product(
        self, user_id: UUID, request: ProductCreateRequest
    ) -> ProductResponse:
        farmer = await self.farmers.get_by_user_id(user_id, for_update=True)
        if farmer is None:
            raise ProductFarmerNotFound
        category = await self.categories.get_active_by_id(request.category_id)
        if category is None:
            raise ProductCategoryNotFound
        self._ensure_can_publish(farmer, request.status)
        product = Product(
            farmer_id=farmer.id,
            category_id=category.id,
            name=request.name,
            description=request.description,
            price=request.price,
            unit=request.unit,
            available_quantity=request.available_quantity,
            image_url=request.image_url,
            status=request.status,
        )
        self.products.add(product)
        await self.session.flush()
        await self.session.commit()
        saved = await self.products.get_for_farmer(product.id, farmer.id)
        assert saved is not None
        return self._detail_response(saved)

    async def update_farmer_product(
        self, user_id: UUID, product_id: UUID, request: ProductUpdateRequest
    ) -> ProductResponse:
        farmer = await self.farmers.get_by_user_id(user_id, for_update=True)
        if farmer is None:
            raise ProductFarmerNotFound
        product = await self.products.get_for_farmer(
            product_id, farmer.id, for_update=True
        )
        if product is None:
            raise ProductNotFound
        values = request.model_dump(exclude_unset=True)
        category = None
        if "category_id" in values:
            category = await self.categories.get_active_by_id(values["category_id"])
            if category is None:
                raise ProductCategoryNotFound
        target_status = values.get("status", product.status)
        if (
            target_status != product.status
            and target_status not in PRODUCT_STATUS_TRANSITIONS[product.status]
        ):
            raise InvalidProductStatusTransition
        self._ensure_can_publish(farmer, target_status)
        for field in (
            "name",
            "description",
            "price",
            "unit",
            "available_quantity",
            "image_url",
            "status",
        ):
            if field in values:
                setattr(product, field, values[field])
        if category is not None:
            product.category_id = category.id
        await self.session.flush()
        await self.session.commit()
        saved = await self.products.get_for_farmer(product.id, farmer.id)
        assert saved is not None
        return self._detail_response(saved)

    async def deactivate_farmer_product(
        self, user_id: UUID, product_id: UUID
    ) -> ProductResponse:
        farmer = await self.farmers.get_by_user_id(user_id, for_update=True)
        if farmer is None:
            raise ProductFarmerNotFound
        product = await self.products.get_for_farmer(
            product_id, farmer.id, for_update=True
        )
        if product is None:
            raise ProductNotFound
        if product.status != ProductStatus.INACTIVE:
            product.status = ProductStatus.INACTIVE
            await self.session.flush()
            await self.session.commit()
        saved = await self.products.get_for_farmer(product.id, farmer.id)
        assert saved is not None
        return self._detail_response(saved)

    async def list_admin_products(self, **filters) -> ProductListResponse:
        products, total = await self.products.list_for_admin(**filters)
        return self._list_response(
            products, total, filters["page"], filters["page_size"]
        )

    async def get_admin_product(self, product_id: UUID) -> ProductResponse:
        product = await self.products.get_for_admin(product_id)
        if product is None:
            raise ProductNotFound
        return self._detail_response(product)

    @staticmethod
    def _ensure_can_publish(farmer: Farmer, status: ProductStatus) -> None:
        if (
            status == ProductStatus.ACTIVE
            and farmer.verification_status != VerificationStatus.COMPLETED
        ):
            raise UnverifiedFarmerCannotPublish

    @staticmethod
    def _validate_price_range(min_price, max_price) -> None:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise InvalidProductPriceRange

    @classmethod
    def _list_response(
        cls, products: list[Product], total: int, page: int, page_size: int
    ) -> ProductListResponse:
        return ProductListResponse(
            items=[cls._list_item(product) for product in products],
            page=page,
            page_size=page_size,
            total=total,
            pages=ceil(total / page_size) if total else 0,
        )

    @staticmethod
    def _list_item(product: Product) -> ProductListItem:
        return ProductListItem(
            id=product.id,
            name=product.name,
            price=product.price,
            unit=product.unit,
            available_quantity=product.available_quantity,
            is_available=product.is_available,
            status=product.status,
            image_url=product.image_url,
            category=ProductCategorySummary(
                id=product.category.id, name=product.category.name
            ),
            farmer=ProductFarmerSummary(
                id=product.farmer.id,
                full_name=product.farmer.full_name,
                farm_name=product.farmer.farm_name,
                farm_location=product.farmer.farm_location,
                farm_image_url=product.farmer.farm_image_url,
                verification_status=product.farmer.verification_status,
            ),
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    @classmethod
    def _detail_response(cls, product: Product) -> ProductResponse:
        return ProductResponse(
            **cls._list_item(product).model_dump(), description=product.description
        )
