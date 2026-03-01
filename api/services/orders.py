from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from database.models import (
    Order,
    OrderFlavor,
    Product,
    Flavor,
    User
)
from bot.loader import bot
from bot.handlers.seller import notify_seller
from fastapi import HTTPException

async def create_order(session: AsyncSession, user: User, product_id: int, flavors_data: list):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    existing_order_stmt = select(Order).where(
        Order.user_id == user.id,
        Order.product_id == product_id,
        Order.status == "pending"
    )
    existing_order = (await session.execute(existing_order_stmt)).scalar_one_or_none()

    if existing_order:
        return {
            "order_id": existing_order.id,
            "seller_tg": "duplicate", 
            "text": "У вас уже есть активный заказ на этот товар. Ожидайте ответа продавца."
        }

    flavor_ids = [f["flavor_id"] for f in flavors_data]
    if not flavor_ids:
        raise HTTPException(status_code=400, detail="Не выбраны вкусы")

    stmt = select(Flavor.id).where(Flavor.id.in_(flavor_ids))
    res = await session.execute(stmt)
    existing_flavor_ids = res.scalars().all()

    for f_id in flavor_ids:
        if f_id not in existing_flavor_ids:
            raise HTTPException(status_code=400, detail=f"Вкус с ID {f_id} не существует")

    order = Order(
        user_id=user.id,
        seller_id=product.seller_id,
        product_id=product.id,
        city_id=product.city_id,
        quantity_tyg=product.quantity_tyg,
        total_price=product.price,
        status="pending"
    )
    session.add(order)
    await session.flush()  

    for f in flavors_data:
        session.add(OrderFlavor(
            order_id=order.id, 
            flavor_id=f["flavor_id"], 
            quantity=f.get("quantity", 1)
        ))

    await session.commit()

    try:
        await notify_seller(bot, session, order.id)
    except Exception as e:
        print(f"Ошибка уведомления: {e}")

    return {
        "order_id": order.id,
        "seller_tg": "notification_sent",
        "text": f"Заказ успешно создан. ID: {order.id}"
    }


async def get_user_orders(
    *,
    session: AsyncSession,
    user: User
):
    """
    Получает заказы пользователя с предварительной загрузкой связанных данных
    """
    # ВАЖНО: Используем selectinload для жадной загрузки product
    query = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(
            selectinload(Order.product),  # Загружаем продукт для каждого заказа
            # Если нужны также вкусы, раскомментируйте:
            # selectinload(Order.flavors).selectinload(OrderFlavor.flavor)
        )
        .order_by(Order.created_at.desc())
    )
    
    result = await session.execute(query)
    orders = result.scalars().all()
    
    return orders


# Альтернативная версия, если нужно загружать также и вкусы:
async def get_user_orders_with_flavors(
    *,
    session: AsyncSession,
    user: User
):
    """
    Получает заказы пользователя с продуктами и вкусами
    """
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
    
    return orders