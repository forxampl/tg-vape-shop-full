from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.deps import get_session
from api.core.AuthMiddleware import get_current_user
from api.schemas.feedback import FeedbackCreateIn
from api.services.feedback import create_feedback

router = APIRouter(tags=["Feedback"])


@router.post("/feedback")
async def send_feedback(
    data: FeedbackCreateIn,
    session: AsyncSession = Depends(get_session),
    user = Depends(get_current_user)
):
    await create_feedback(
        session=session,
        user=user,
        text=data.text
    )
    return {"status": "sent"}
