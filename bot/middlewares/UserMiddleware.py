from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Seller
from bot.middlewares.translator import ctx_lang 


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        
        session: AsyncSession = data.get("session")
        tg_user: TgUser = data.get("event_from_user")

        if not tg_user or not session:
            return await handler(event, data)

        result = await session.execute(
            select(User).where(User.tg_id == tg_user.id)
        )
        user = result.scalars().first()
        
        full_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip()

        if not user:
            user = User(
                tg_id=tg_user.id,
                username=tg_user.username,
                full_name=full_name,
                role="user",
                language="ru"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        else:
            updated = False

            if user.username != tg_user.username:
                user.username = tg_user.username
                updated = True

            if user.full_name != full_name:
                user.full_name = full_name
                updated = True

            if updated:
                await session.commit()

        data["user"] = user

        user_lang = user.language if user.language else "ru"
        ctx_lang.set(user_lang)

        if user.role in ["seller", "super_admin"]:
            seller_obj = await session.scalar(
                select(Seller).where(Seller.user_id == user.id)
            )
            
            if not seller_obj:
                seller_obj = Seller(user_id=user.id)
                session.add(seller_obj)
                await session.flush()
            
            data["seller"] = seller_obj
        else:
            data["seller"] = None

        return await handler(event, data)
