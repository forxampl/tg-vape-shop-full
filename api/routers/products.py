from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_session
from api.schemas.products import (
    ProductListOut,
    ProductDetailOut,
)
from api.services import products as product_service

router = APIRouter(tags=["Products"])

@router.get(
    "/products",
    response_model=list[ProductListOut]
)
async def products_list(
    city_id: int = Query(...),
    strength: int | None = None,
    puffs: int | None = None,
    brand: str | None = None,
    seller_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    products = await product_service.get_products(
        session=session,
        city_id=city_id,
        strength=strength,
        puffs=puffs,
        brand=brand,
        seller_id=seller_id
    )

    return [
        ProductListOut(
            id=p.id,
            name=p.name,
            price=float(p.price),
            puffs=p.quantity_tyg,
            strength=p.strength_mg,
            brand=p.brand,
            in_stock=p.in_stock,
            image=p.image_path
        )
        for p in products
    ]


@router.get(
    "/products/{product_id}",
    response_model=ProductDetailOut
)
async def product_detail(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    data = await product_service.get_product_detail(
        session=session,
        product_id=product_id
    )

    if not data:
        raise HTTPException(404, "Product not found")

    product, flavors = data

    return ProductDetailOut(
        id=product.id,
        name=product.name,
        price=float(product.price),
        puffs=product.quantity_tyg,
        strength=product.strength_mg,
        brand=product.brand,
        in_stock=product.in_stock,
        image=product.image_path,
        flavors=[
            {"id": f.id, "name": f.name}
            for f in flavors
        ],
        seller_id=product.seller_id,
        city_id=product.city_id
    )