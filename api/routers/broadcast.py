from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from api.core.deps import get_session
from api.schemas.broadcast import BroadcastToggleIn, BroadcastStateOut
from api.services.broadcast import set_broadcast_state
from api.core.AuthMiddleware import get_current_user 
from database.models import User

router = APIRouter(tags=["Broadcast"])

@router.post("/broadcast")
async def toggle_broadcast(
    data: BroadcastToggleIn, 
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user) 
):
    await set_broadcast_state(session=session, user=user, enabled=data.enabled)
    return {"ok": True}

@router.get("/broadcast", response_model=BroadcastStateOut)
async def fetch_broadcast_state(
    user: User = Depends(get_current_user) 
):
    return {"enabled": user.broadcast_enabled}