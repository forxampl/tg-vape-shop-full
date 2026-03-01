from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import City, Product
from bot.middlewares.translator import _, ctx_lang

def seller_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("add_product_btn"), callback_data="seller_add")],
        [InlineKeyboardButton(text=_("edit_product_btn"), callback_data="seller_edit")],
        [InlineKeyboardButton(text=_("my_products_btn"), callback_data="seller_orders")],
        [InlineKeyboardButton(text=_("stats_btn"), callback_data="seller_stats")],
    ])

def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data="seller_cancel")]
    ])


async def cities_kb(session: AsyncSession) -> InlineKeyboardMarkup:
    result = await session.execute(select(City))
    cities = result.scalars().all()

    lang = ctx_lang.get()
    kb = []

    for city in cities:
        city_name = city.name_lv if lang == "lv" else city.name_ru

        kb.append([
            InlineKeyboardButton(
                text=city_name,
                callback_data=f"city_{city.id}"
            )
        ])

    kb.append([
        InlineKeyboardButton(text=_("cancel_btn"), callback_data="seller_cancel")
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

async def brands_kb(session: AsyncSession) -> InlineKeyboardMarkup:

    result = await session.execute(select(Product.brand).distinct())
    brands = [b[0] for b in result.all() if b[0]] 

    kb = [[InlineKeyboardButton(text=brand, callback_data=f"brand_{brand}")] for brand in brands]
    kb.append([InlineKeyboardButton(text=_("cancel_btn"), callback_data="seller_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def strengths_kb():
    strengths = ["20","50"]
    kb = [[InlineKeyboardButton(text=s, callback_data=f"strength_{s}")] for s in strengths]
    kb.append([InlineKeyboardButton(text=_("cancel_btn"), callback_data="seller_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("add_btn"), callback_data="confirm_add")],
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data="seller_cancel")]
    ])
    return kb


async def edit_cities_kb(seller_id: int, session: AsyncSession) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    result = await session.execute(
        select(City)
        .join(Product)
        .where(Product.seller_id == seller_id)
        .distinct()
    )
    cities = result.scalars().all()

    lang = ctx_lang.get()

    for city in cities:
        city_name = city.name_lv if lang == "lv" else city.name_ru

        kb.inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text=city_name,
                    callback_data=f"edit_city_{city.id}"
                )
            ]
        )

    kb.inline_keyboard.append(
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data="seller_cancel")]
    )

    return kb


async def edit_products_kb(seller_id: int, city_id: int, session: AsyncSession) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    result = await session.execute(
        select(Product).where(Product.seller_id == seller_id, Product.city_id == city_id)
    )
    products = result.scalars().all()

    for p in products:
        kb.inline_keyboard.append(
            [InlineKeyboardButton(text=p.name, callback_data=f"edit_product_{p.id}")]
        )


    kb.inline_keyboard.append(
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data="seller_cancel")]
    )
    return kb


def edit_product_actions_kb(product_id: int, is_available: bool):
    stock_text = _("status_in_stock") if is_available else _("status_out_of_stock")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=stock_text, callback_data=f"sel_act:toggle:{product_id}")],
            [
                InlineKeyboardButton(text=_("redact_add_flavor_btn"), callback_data=f"sel_act:add_fl:{product_id}"),
                InlineKeyboardButton(text=_("redact_del_flavor_btn"), callback_data=f"sel_act:rem_fl:{product_id}"),
            ],
            [
                InlineKeyboardButton(text=_("redact_name_btn"), callback_data=f"sel_act:edit:name:{product_id}"),
                InlineKeyboardButton(text=_("redact_brand_btn"), callback_data=f"sel_act:edit:brand:{product_id}")
            ],
            [
                InlineKeyboardButton(text=_("redact_tygs_btn"), callback_data=f"sel_act:edit:puffs:{product_id}"),
                InlineKeyboardButton(text=_("redact_strenght_btn"), callback_data=f"sel_act:edit:strength:{product_id}")
            ],
            [
                InlineKeyboardButton(text=_("redact_price_btn"), callback_data=f"sel_act:edit:price:{product_id}"),
                InlineKeyboardButton(text=_("redact_photo_btn"), callback_data=f"sel_act:photo:{product_id}")
            ],
            [InlineKeyboardButton(text=_("delete_product_btn"), callback_data=f"sel_act:delete:{product_id}")],
            [InlineKeyboardButton(text=_("back_from_edit_btn"), callback_data="seller_edit")]
        ]
    )


def new_order_kb(order_id: int):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("confirm_order_btn"), callback_data=f"order:confirm:{order_id}"),
                InlineKeyboardButton(text=_("cancel_order_btn"), callback_data=f"order:cancel:{order_id}")
            ]
        ]
    )
    return kb


def order_card_kb(order):
    if order.status == "pending":
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("confirm_order_btn"),
                    callback_data=f"order:confirm:{order.id}"
                ),
                InlineKeyboardButton(
                    text=_("cancel_order_btn"),
                    callback_data=f"order:cancel:{order.id}"
                )
            ]
        ])

    if order.status == "confirmed":
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("complete_btn"),
                    callback_data=f"order:complete:{order.id}"
                ),
                InlineKeyboardButton(
                    text=_("canceled_btn"),
                    callback_data=f"order:cancel:{order.id}"
                )
            ]
        ])

    return None
