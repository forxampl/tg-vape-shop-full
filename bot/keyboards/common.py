from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from bot.middlewares.translator import _

from aiogram.types import MenuButtonWebApp, WebAppInfo
def age_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data="age_yes"),
            InlineKeyboardButton(text="❌", callback_data="age_no")
        ]
    ])

def language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="Latviešu", callback_data="lang_lv")
        ]
    ])


def main_menu_kb() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("btn_change_lang"))
            ]
        ],
        resize_keyboard=True,  
        one_time_keyboard=False
    )