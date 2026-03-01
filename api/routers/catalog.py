from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import City, Product, Flavor
from fastapi.responses import Response, JSONResponse
from bot.main import bot
from api.core.deps import get_session 
from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from api.core.AuthMiddleware import get_current_user 
import json
import logging

router = APIRouter(prefix="/api", tags=["catalog"])


class ProductResponse(BaseModel):
    id: int
    name: str
    city_id: int
    seller_id: int | None = None
    price: Decimal 
    brand: str | None = None
    strength_mg: int | None = None
    image_path: str | None = None
    in_stock: bool

    model_config = ConfigDict(from_attributes=True)


@router.get("/cities")
async def get_cities(
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user) 
):
    try:
        result = await session.execute(select(City))
        cities = result.scalars().all()
        
        # Преобразуем в список словарей для полного контроля сериализации
        cities_data = []
        for city in cities:
            cities_data.append({
                "id": city.id,
                "name": city.name,
                "created_at": str(city.created_at) if city.created_at else None
            })
        
        return JSONResponse(
            content=cities_data,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        logging.error(f"Error in get_cities: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


@router.get("/brands") 
async def get_brands(session: AsyncSession = Depends(get_session)):
    try:
        query = select(Product.brand).distinct().where(Product.brand != None)
        result = await session.execute(query)
        brands = result.scalars().all()
        
        print(f"DEBUG BRANDS: Найдено брендов в базе: {brands}")
        
        # Фильтруем None значения
        brands = [brand for brand in brands if brand is not None]
        
        return JSONResponse(
            content=brands,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        logging.error(f"Error in get_brands: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


@router.get("/products")
async def get_products(
    city_id: int = Query(..., description="ID города"),
    brand: str = Query(None, description="Фильтр по бренду"),
    strength: str = Query(None, description="Фильтр по крепости (через запятую)"),
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user) 
):
    try:
        query = select(Product).where(Product.city_id == city_id)
        
        if brand and brand != "Все" and brand.lower() != "all":
            query = query.where(Product.brand == brand)
        
        # Добавляем фильтр по крепости если нужно
        if strength:
            strengths = strength.split(',')
            if strengths:
                query = query.where(Product.strength_mg.in_([int(s) for s in strengths if s]))
        
        result = await session.execute(query)
        products = result.scalars().all()
        
        # Преобразуем в список словарей для правильной сериализации
        products_data = []
        for product in products:
            product_dict = {
                "id": product.id,
                "name": product.name,
                "city_id": product.city_id,
                "seller_id": product.seller_id,
                "price": float(product.price) if product.price else 0,  # Decimal -> float для JSON
                "brand": product.brand,
                "strength_mg": product.strength_mg,
                "image_path": product.image_path,
                "in_stock": product.in_stock
            }
            products_data.append(product_dict)
        
        return JSONResponse(
            content={
                "success": True,
                "data": products_data
            },
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        logging.error(f"Error in get_products: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            },
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


@router.get("/products/{product_id}/flavors")
async def get_flavors(
    product_id: int, 
    session: AsyncSession = Depends(get_session)
):
    try:
        result = await session.execute(
            select(Flavor).where(Flavor.product_id == product_id)
        )
        flavors = result.scalars().all()
        
        # Преобразуем в список словарей
        flavors_data = []
        for flavor in flavors:
            flavors_data.append({
                "id": flavor.id,
                "name": flavor.name,
                "product_id": flavor.product_id,
                "is_available": flavor.is_available
            })
        
        return JSONResponse(
            content=flavors_data,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        logging.error(f"Error in get_flavors: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )


@router.get("/get_image/{file_id}")
async def get_image(file_id: str):
    try:
        file = await bot.get_file(file_id)
        file_bytes = await bot.download_file(file.file_path)
        
        # Определяем тип изображения по расширению
        content_type = "image/jpeg"
        if file.file_path and file.file_path.lower().endswith('.png'):
            content_type = "image/png"
        elif file.file_path and file.file_path.lower().endswith('.gif'):
            content_type = "image/gif"
            
        return Response(
            content=file_bytes.getvalue(), 
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000",
                "Content-Type": content_type
            }
        )
    except Exception as e:
        logging.error(f"Error getting image {file_id}: {e}")
        return Response(status_code=404)


# Добавляем health check endpoint
@router.get("/health")
async def health_check():
    return JSONResponse(
        content={"status": "ok"},
        headers={"Content-Type": "application/json; charset=utf-8"}
    )