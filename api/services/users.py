from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User


async def get_profile(user: User):
    return user


async def set_language(
    *,
    session: AsyncSession,
    user: User,
    language: str
):
    user.language = language
    await session.commit()


