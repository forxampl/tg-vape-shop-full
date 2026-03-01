from urllib.parse import parse_qs, unquote
import json
import hmac
import hashlib
from fastapi import Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User
from api.core.deps import get_session
from config import BOT_TOKEN 

def verify_telegram_data(init_data: str) -> dict:
    try:
        parsed_data = parse_qs(init_data)
        user_json = parsed_data.get('user')[0]
        return json.loads(unquote(user_json))
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        raise HTTPException(status_code=403, detail="Invalid Data Format")

async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session)
): 
    init_data = request.headers.get("X-TG-Data")
    if not init_data:
        raise HTTPException(401, "No Telegram Init Data provided")

    tg_user = verify_telegram_data(init_data)
    tg_id = int(tg_user["id"])

    result = await session.execute(
        select(User).where(User.tg_id == tg_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            tg_id=tg_id,
            username=tg_user.get("username"),
            full_name=f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip(),
            role="user",
            language=tg_user.get("language_code", "ru")
        )
        session.add(user)
        await session.commit()

    return user