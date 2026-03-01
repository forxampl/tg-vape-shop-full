from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from database.database import SessionLocal

class DBMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        async with SessionLocal() as session:
            data["session"] = session
            try:
                res = await handler(event, data)
                await session.commit() 
                return res
            except Exception as e:
                await session.rollback() 
                raise e