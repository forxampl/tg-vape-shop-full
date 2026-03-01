from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from api.core.deps import get_session
from api.core.AuthMiddleware import get_current_user
from api.schemas.orders import (
    OrderCreateIn,
    OrderCreateOut,
    OrderOut,
)
from api.services.orders import create_order, get_user_orders
from database.models import Order, OrderFlavor

router = APIRouter(tags=["Orders"])


@router.post("/orders", response_model=OrderCreateOut)
async def create_order_endpoint(
    data: OrderCreateIn,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user)
):
    order_data = await create_order(
        session=session,
        user=user,
        product_id=data.product_id,
        flavors_data=[f.dict() for f in data.flavors]
    )

    return OrderCreateOut(**order_data)


@router.get("/orders/my", response_model=list[OrderOut])
async def my_orders(
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user)
):
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    
    # Выполняем запрос прямо здесь с правильной загрузкой
    query = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(
            selectinload(Order.product)  # обязательно!
        )
        .order_by(Order.created_at.desc())
    )
    
    result = await session.execute(query)
    orders = result.scalars().all()
    
    # Принудительно загружаем все связанные данные перед закрытием сессии
    for o in orders:
        _ = o.product.name  # триггерим загрузку
    
    return [
        OrderOut(
            id=o.id,
            product_id=o.product_id,
            product_name=o.product.name,  # теперь должно работать
            total_price=float(o.total_price),
            created_at=o.created_at
        )
        for o in orders
    ]


# Если нужно больше данных (например, с флагами), можно добавить отдельный endpoint:
@router.get("/orders/my/detailed", response_model=list[OrderOut])
async def my_orders_detailed(
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user)
):
    # Кастомный запрос с жадной загрузкой всех данных
    query = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(
            selectinload(Order.product),
            selectinload(Order.flavors).selectinload(OrderFlavor.flavor)
        )
        .order_by(Order.created_at.desc())
    )
    
    result = await session.execute(query)
    orders = result.scalars().all()
    
    result_list = []
    for o in orders:
        order_dict = {
            "id": o.id,
            "product_id": o.product_id,
            "product_name": o.product.name,
            "total_price": float(o.total_price),
            "created_at": o.created_at,
            "flavors": []
        }
        
        # Добавляем информацию о вкусах
        for of in o.flavors:
            if of.flavor:
                order_dict["flavors"].append({
                    "flavor_id": of.flavor_id,
                    "flavor_name": of.flavor.name,
                    "quantity": of.quantity
                })
        
        result_list.append(OrderOut(**order_dict))
    
    return result_list