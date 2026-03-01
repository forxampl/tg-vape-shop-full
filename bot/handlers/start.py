from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.start import StartStates
from bot.keyboards.common import age_kb, language_kb, main_menu_kb
from database.models import User
from bot.middlewares.translator import _, ctx_lang 
from aiogram.filters import Command
from bot.loader import bot
from aiogram.types import MenuButtonWebApp, WebAppInfo
from config import MINI_APP_URL
router = Router()

async def set_miniapp_menu_button(user_id: int):
    await bot.set_chat_menu_button(
        chat_id=user_id,
        menu_button=MenuButtonWebApp(
            text=_("open_miniapp"),
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    )

@router.message(Command("start"))
async def start(message: Message, state: FSMContext, user: User):
    await state.clear()

    if user and user.age_confirmed:
        ctx_lang.set(user.language)

        await set_miniapp_menu_button(message.from_user.id)

        await message.answer(
            _("welcome_final"),
            reply_markup=main_menu_kb()
)
        return

    await state.set_state(StartStates.confirm_age)
    username = user.username or message.from_user.first_name
    await message.answer(_("welcome_age", username=username), reply_markup=age_kb())

@router.callback_query(F.data == "age_no")
async def age_no(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(_("access_denied"))

@router.callback_query(F.data == "age_yes")
async def age_yes(call: CallbackQuery, state: FSMContext, user: User, session):
    user.age_confirmed = True
    await session.commit()

    await state.set_state(StartStates.choose_language)
    await call.message.edit_text(_("choose_lang"), reply_markup=language_kb())

@router.callback_query(F.data.startswith("lang_"))
async def choose_lang(call: CallbackQuery, state: FSMContext, session, user: User):
    lang = call.data.split("_")[1]
    

    if user:
        user.language = lang
        await session.commit()
    
    ctx_lang.set(lang)
    await state.clear()
    
    await set_miniapp_menu_button(call.from_user.id)

    await call.message.answer(
        _("welcome_final")
    )


@router.message(F.text.in_([
    _("btn_change_lang", locale="ru"),
    _("btn_change_lang", locale="lv"),
    "🌐 Сменить язык",
    "🌐 Mainīt valodu"
]))
async def language_button_handler(message: Message, state: FSMContext):
    await state.set_state(StartStates.choose_language)
    await message.answer(
        _("choose_lang"),
        reply_markup=language_kb()
    )


