from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import City

async def get_all_cities(session: AsyncSession, lang: str = "ru"):
    order_col = City.name_lv if lang == "lv" else City.name_ru
    result = await session.execute(select(City).order_by(order_col))
    return result.scalars().all()

async def create_city(session: AsyncSession, name_ru: str, name_lv: str):
    city = City(name_ru=name_ru, name_lv=name_lv)
    session.add(city)
    await session.commit()
    return city

async def delete_city(session: AsyncSession, city_id: int):
    city = await session.get(City, city_id)
    if city:
        await session.delete(city)
        await session.commit()
    return True