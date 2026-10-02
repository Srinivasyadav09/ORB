"""Seed fake marketplace records in development or test environments only.

Run explicitly with `python scripts/seed_marketplace.py`. Active sample products
are assigned only to an existing farmer whose verification is COMPLETED.
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionFactory, engine
from app.models.category import Category
from app.models.farmer import Farmer, VerificationStatus
from app.models.product import Product, ProductStatus, ProductUnit

CATEGORY_NAMES = (
    "Vegetables",
    "Fruits",
    "Leafy Greens",
    "Grains",
    "Pulses",
    "Dairy",
    "Other",
)

SAMPLE_PRODUCTS = (
    (
        "Tomatoes",
        "Vegetables",
        "40.00",
        "kg",
        "25.000",
        "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=800&q=85",
    ),
    (
        "Potatoes",
        "Vegetables",
        "30.00",
        "kg",
        "40.000",
        "https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=800&q=85",
    ),
    (
        "Red Onions",
        "Vegetables",
        "32.00",
        "kg",
        "32.000",
        "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=800&q=85",
    ),
    (
        "Carrots",
        "Vegetables",
        "50.00",
        "kg",
        "18.000",
        "https://images.unsplash.com/photo-1445282768818-728615cc910a?auto=format&fit=crop&w=800&q=85",
    ),
    (
        "Spinach",
        "Leafy Greens",
        "20.00",
        "bunch",
        "45.000",
        "https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=800&q=85",
    ),
    (
        "Apples",
        "Fruits",
        "120.00",
        "kg",
        "20.000",
        "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=800&q=85",
    ),
    (
        "Cauliflower",
        "Vegetables",
        "35.00",
        "kg",
        "21.000",
        "https://images.unsplash.com/photo-1568584711271-0a1d4e7f9d20?auto=format&fit=crop&w=800&q=85",
    ),
)


async def main() -> None:
    if settings.ENVIRONMENT.lower() == "production":
        raise SystemExit("Marketplace seed data is disabled in production.")
    try:
        async with AsyncSessionFactory() as session, session.begin():
            categories: dict[str, Category] = {}
            for name in CATEGORY_NAMES:
                category = await session.scalar(
                    select(Category).where(Category.name.ilike(name))
                )
                if category is None:
                    category = Category(
                        name=name, description=f"Development category: {name}"
                    )
                    session.add(category)
                    await session.flush()
                categories[name] = category

            farmer = await session.scalar(
                select(Farmer)
                .where(Farmer.verification_status == VerificationStatus.COMPLETED)
                .order_by(Farmer.created_at)
                .limit(1)
            )
            if farmer is None:
                print(
                    "Categories seeded. No products added: verify a development farmer first, then rerun."
                )
                return

            for (
                name,
                category_name,
                price,
                unit,
                quantity,
                image_url,
            ) in SAMPLE_PRODUCTS:
                product = await session.scalar(
                    select(Product).where(
                        Product.farmer_id == farmer.id, Product.name == name
                    )
                )
                values = dict(
                    category_id=categories[category_name].id,
                    description=f"Fresh development sample: {name.lower()} from a local farm.",
                    price=Decimal(price),
                    unit=ProductUnit(unit),
                    available_quantity=Decimal(quantity),
                    image_url=image_url,
                    status=ProductStatus.ACTIVE,
                )
                if product is None:
                    session.add(Product(farmer_id=farmer.id, name=name, **values))
                else:
                    for key, value in values.items():
                        setattr(product, key, value)
        print(
            f"Seeded {len(CATEGORY_NAMES)} categories and {len(SAMPLE_PRODUCTS)} products for a verified development farmer."
        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
