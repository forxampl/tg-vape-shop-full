from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Feedback, User
from bot.handlers.admin import notify_admins_new_feedback
from database.models import Feedback, User
from sqlalchemy.ext.asyncio import AsyncSession
from bot.handlers.admin import notify_admins_new_feedback


async def create_feedback(
    *,
    session: AsyncSession,
    user: User,
    text: str
):
    feedback = Feedback(
        user_id=user.id,
        message=text
    )
    session.add(feedback)
    await session.flush()   
    await session.commit()

    try:
        await notify_admins_new_feedback(
            session=session,
            feedback_id=feedback.id
        )
    except Exception as e:
        print(f"Ошибка уведомления админов: {e}")

    return feedback
