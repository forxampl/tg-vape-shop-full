from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from database.models import Product, City, Order, Feedback
from sqlalchemy.ext.asyncio import AsyncSession
from bot.middlewares.translator import _, ctx_lang
from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("admin_cities_btn"), callback_data="admin_cities")],
        [InlineKeyboardButton(text=_("admin_members_btn"), callback_data="admin_roles")],
        [InlineKeyboardButton(text=_("admin_products_btn"), callback_data="admin_edit")],
        [InlineKeyboardButton(text=_("admin_orders_btn"), callback_data="admin_orders")],
        [InlineKeyboardButton(text=_("feedbacks_btn"), callback_data="admin_feedbacks")],
        [InlineKeyboardButton(text=_("admin_broadcast_btn"), callback_data="admin_broadcast")]
    ])

def admin_products_management_kb():
    buttons = [
        [InlineKeyboardButton(text=_("admin_edit_products_btn"), callback_data="admin_edit_products")],
        [InlineKeyboardButton(text=_("admin_add_for_seller_btn"), callback_data="admin_add_for_seller")],
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_cities_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("add_city_btn"), callback_data="add_city_start")],
        [InlineKeyboardButton(text=_("delete_city_btn"), callback_data="del_city_start")],
        [InlineKeyboardButton(text=_("back_btn"), callback_data="admin_back")]
    ])

def admin_members_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("change_role_btn"), callback_data="admin_roles_start")],
        [InlineKeyboardButton(text=_("back_btn"), callback_data="admin_back")]
    ])

def confirm_broadcast_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("broadcast_send_btn"), callback_data="broadcast_confirm_send")],
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data="admin_back")]
    ])

def admin_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data="admin_back")]
    ])

def admin_edit_cancel_kb(product_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data=f"edt_prod:{product_id}")]
    ])


def admin_sellers_kb(sellers):
    buttons = []

    for s in sellers:
        name = f"ID: {s.id}"
        fullname = ""

        if s.user:
            name = f"@{s.user.username}" if s.user.username else s.user.full_name
            fullname = s.user.full_name or ""

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {name} {fullname}",
                callback_data=f"edt_sel:{s.id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text=_("back_to_products_btn"), callback_data="admin_back")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def admin_cities_select_kb(session: AsyncSession) -> InlineKeyboardMarkup:
    result = await session.execute(select(City))
    cities = result.scalars().all()

    kb = []
    lang = ctx_lang.get()

    for city in cities:
        city_name = city.name_lv if lang == "lv" else city.name_ru

        kb.append([
            InlineKeyboardButton(
                text=city_name,
                callback_data=f"city_{city.id}"
            )
        ])

    kb.append([
        InlineKeyboardButton(
            text=_("cancel_btn"),
            callback_data="admin_back"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_products_kb(products, seller_id):
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"📦 {p.name}", callback_data=f"edt_prod:{p.id}")])
    
    buttons.append([InlineKeyboardButton(text=_("back_to_products_btn"), callback_data="admin_edit_start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/admin")]
        ],
        resize_keyboard=True
    )

def get_product_edit_kb(product):
    p_id = product.id
    stock_text = _("status_in_stock") if product.in_stock else _("status_out_of_stock")
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=stock_text, callback_data=f"adm_act:toggle_stock:{p_id}")],
        [
            InlineKeyboardButton(text=_("add_flavor_btn"), callback_data=f"adm_act:add_flavor:{p_id}"),
            InlineKeyboardButton(text=_("remove_flavor_btn"), callback_data=f"adm_act:del_flavor:{p_id}")
        ],
        [
            InlineKeyboardButton(text=_("edit_name_btn"), callback_data=f"adm_act:edit:name:{p_id}"),
            InlineKeyboardButton(text=_("edit_brand_btn"), callback_data=f"adm_act:edit:brand:{p_id}")
        ],
        [
            InlineKeyboardButton(text=_("edit_puffs_btn"), callback_data=f"adm_act:edit:puffs:{p_id}"),
            InlineKeyboardButton(text=_("edit_strength_btn"), callback_data=f"adm_act:edit:strength:{p_id}")
        ],
        [
            InlineKeyboardButton(text=_("edit_price_btn"), callback_data=f"adm_act:edit:price:{p_id}"),
            InlineKeyboardButton(text=_("edit_photo_btn"), callback_data=f"adm_act:photo:{p_id}")
        ],
        [InlineKeyboardButton(text=_("delete_product_btn"), callback_data=f"adm_act:delete_prod:{p_id}")],
        [InlineKeyboardButton(text=_("back_to_product_list_btn"), callback_data=f"edt_sel:{product.seller_id}")]
    ])

def admin_confirm_add_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("confirm_add_btn"), callback_data="admin_confirm_add"),
                InlineKeyboardButton(text=_("cancel_btn"), callback_data="admin_back")
            ]
        ]
    )


async def admin_brands_kb(session: AsyncSession) -> InlineKeyboardMarkup:
    result = await session.execute(select(Product.brand).distinct())
    brands = [b[0] for b in result.all() if b[0]]

    kb = []
    for brand in brands:
        kb.append([
            InlineKeyboardButton(
                text=brand,
                callback_data=f"adm_brand:{brand}"
            )
        ])


    kb.append([
        InlineKeyboardButton(
            text=_("cancel_btn"),
            callback_data="admin_back"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)



def admin_feedback_actions_kb(
    feedback_id: int,
    processed: bool = False
):
    keyboard = []

    if not processed:
        keyboard.append([
            InlineKeyboardButton(
                text=_("reply_feedback_btn"),
                callback_data=f"admin_fb_reply:{feedback_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text=_("delete_feedback_btn"),
            callback_data=f"admin_fb_del:{feedback_id}"
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            text=_("back_feedbacks"),
            callback_data="admin_feedbacks"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)





def admin_feedbacks_list_kb(feedbacks: list[Feedback]):
    kb = InlineKeyboardBuilder()

    for f in feedbacks:
        icon = "💬 " if not f.is_processed else "✅ "

        kb.button(
            text=f"{icon}#{f.id}",
            callback_data=f"admin_fb:{f.id}"
        )

    kb.adjust(1)

    kb.row(
        InlineKeyboardButton(
            text=_("back_btn"),
            callback_data="admin_back"
        )
    )

    return kb.as_markup()




def admin_orders_list_kb(orders: list[Order]):
    kb = InlineKeyboardBuilder()

    for o in orders:
        kb.button(
            text=_(
                "admin_order_item",
                id=o.id,
                status=o.status
            ),
            callback_data=f"admin_order:{o.id}"
        )

    kb.adjust(1)

    kb.row(
        InlineKeyboardButton(
            text=_("back_btn"),
            callback_data="admin_back"
        )
    )

    return kb.as_markup()



def admin_order_card_kb(order_id: int, status: str):
    kb = InlineKeyboardBuilder()

    if status == "pending":
        kb.button(
            text=_("order_confirm_btn"),
            callback_data=f"admin_order:confirm:{order_id}"
        )
        kb.button(
            text=_("order_cancel_btn"),
            callback_data=f"admin_order:cancel:{order_id}"
        )

    kb.button(
        text=_("back_btn"),
        callback_data="admin_orders"
    )

    kb.adjust(2)

    return kb.as_markup()

def confirm_city_translation_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=_("btn_confirm_city"), callback_data="city_confirm_yes"),
            InlineKeyboardButton(text=_("btn_manual_city"), callback_data="city_confirm_no"),
        ]
    ])