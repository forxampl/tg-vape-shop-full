from urllib.parse import parse_qs, unquote
import json
from fastapi import HTTPException
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from config import BOT_TOKEN
from aiogram.utils.web_app import check_webapp_signature


async def set_broadcast_state(session: AsyncSession, init_data: str, enabled: bool):
    is_valid = check_webapp_signature(BOT_TOKEN, init_data)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid WebApp signature")

    parsed = parse_qs(init_data)
    user_json = parsed.get("user", [None])[0]
    if not user_json:
        raise HTTPException(status_code=400, detail="User data missing")

    user_data = json.loads(unquote(user_json))
    tg_id = int(user_data["id"])

    result = await session.execute(
        update(User)
        .where(User.tg_id == tg_id)
        .values(broadcast_enabled=enabled)
    )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

async def set_broadcast_state(session: AsyncSession, user: User, enabled: bool):
    user.broadcast_enabled = enabled
    await session.commit()


async def get_broadcast_state(session: AsyncSession, init_data: str) -> bool:
    is_valid = check_webapp_signature(BOT_TOKEN, init_data)
    if not is_valid:
        raise HTTPException(status_code=403, detail="Invalid WebApp signature")

    parsed = parse_qs(init_data)
    user_json = parsed.get("user", [None])[0]
    if not user_json:
        raise HTTPException(status_code=400, detail="User data missing")

    user_data = json.loads(unquote(user_json))
    tg_id = int(user_data["id"])

    user = await session.scalar(
        select(User).where(User.tg_id == tg_id)
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.broadcast_enabled