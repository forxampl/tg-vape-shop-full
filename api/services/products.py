from sqlalchemy import select, desc, case
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product, Flavor


async def get_products(
    *,
    session: AsyncSession,
    city_id: int,
  
    strength: int | None = None,
    puffs: int | None = None,
    brand: str | None = None,
    seller_id: int | None = None,
):
    query = select(Product).filter(Product.city_id == city_id)
    stmt = select(Product).where(Product.city_id == city_id)

    if strength:
        stmt = stmt.where(Product.strength_mg == strength)

    if puffs:
        stmt = stmt.where(Product.quantity_tyg == puffs)

    if brand:
        stmt = stmt.where(Product.brand == brand)

    if seller_id:
        stmt = stmt.where(Product.seller_id == seller_id)

    stmt = stmt.order_by(
        case((Product.in_stock == True, 0), else_=1),
        desc(Product.created_at)
    )
    query = query.order_by(Product.in_stock.desc(), Product.created_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


async def get_product_detail(
    *,
    session: AsyncSession,
    product_id: int
):
    product = await session.get(Product, product_id)
    if not product:
        return None

    result = await session.execute(
        select(Flavor).where(Flavor.product_id == product_id)
    )
    flavors = result.scalars().all()

    return product, flavors