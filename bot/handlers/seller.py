import asyncio
from PIL import Image
from io import BytesIO
from decimal import Decimal
from aiogram import Router, F
from sqlalchemy import select, delete, desc, func
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Seller, City, Product, Flavor, Order, OrderFlavor
from bot.states.seller import SellerAddProduct, SellerEditProduct
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, BufferedInputFile, InlineKeyboardMarkup,InlineKeyboardButton
from bot.keyboards.seller import seller_panel_kb, cancel_kb, cities_kb, brands_kb, strengths_kb, confirm_kb, edit_cities_kb, edit_products_kb, edit_product_actions_kb, order_card_kb
from bot.middlewares.translator import _, ctx_lang
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from aiogram import Bot
from sqlalchemy.orm import selectinload




class IsSeller(BaseFilter):
    
    async def __call__(self, message: Message, user: User) -> bool:
        return user.role in ["seller", "super_admin"]
    
seller_router = Router()
seller_router.message.filter(IsSeller())
seller_router.callback_query.filter(IsSeller())
    
@seller_router.message(F.text == "/seller")
async def seller_panel(msg: Message, user: User, seller: Seller | None):
    await msg.answer(_("seller_panel"), reply_markup=seller_panel_kb())

@seller_router.callback_query(F.data == "seller_panel")
async def back_to_seller_panel(cb: CallbackQuery):
    await cb.message.edit_text(_("seller_panel"), reply_markup=seller_panel_kb())
    await cb.answer()

@seller_router.callback_query(F.data == "seller_cancel")
async def seller_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    
    kb = seller_panel_kb()

    if cb.message.photo:
        await cb.message.delete()   
        await cb.message.answer(
        _("action_cancelled"), 
        reply_markup=seller_panel_kb()
    )
        
    else: 
        await cb.message.edit_text(_("seller_panel") , reply_markup=kb)

@seller_router.callback_query(F.data == "seller_add")
async def add_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession):

    await state.set_state(SellerAddProduct.city)


    kb = await cities_kb(session)


    msg = await cb.message.edit_text(_("add_product_start"), reply_markup=kb)

    await state.update_data(bot_msg_id=msg.message_id)

@seller_router.callback_query(F.data.startswith("city_"))
async def add_city(cb: CallbackQuery, state: FSMContext):
    try:
        city_id = int(cb.data.split("_")[1])
    except (IndexError, ValueError):
        await cb.answer("Ошибка выбора города", show_alert=True)
        return

    await state.update_data(city_id=city_id)
    await state.set_state(SellerAddProduct.name)

    await cb.message.edit_text(
        _("enter_name"),
        reply_markup=cancel_kb()
    )

    await cb.answer()


@seller_router.message(SellerAddProduct.name)
async def add_name(msg: Message, state: FSMContext, session: AsyncSession):
    if len(msg.text) > 25:
        await msg.delete()
        return

    await state.update_data(name=msg.text)
    await msg.delete()

    data = await state.get_data()

    kb = await brands_kb(session)

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("choose_brand"),
        reply_markup=kb
    )

    await state.set_state(SellerAddProduct.brand)


@seller_router.callback_query(F.data.startswith("brand_"))
async def add_brand_btn(cb: CallbackQuery, state: FSMContext):
    brand = cb.data.replace("brand_", "")

    await state.update_data(brand=brand)
    await state.set_state(SellerAddProduct.puffs)

    await cb.message.edit_text(
        _("enter_puffs"),
        reply_markup=cancel_kb()
    )

@seller_router.message(SellerAddProduct.brand)
async def add_brand_text(msg: Message, state: FSMContext):
    if not msg.text:
        return

    data = await state.get_data()
    await state.update_data(brand=msg.text)
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("enter_puffs"),
        reply_markup=cancel_kb()
    )

    await state.set_state(SellerAddProduct.puffs)



@seller_router.message(SellerAddProduct.puffs)
async def add_puffs(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        error = await msg.answer(_("invalid_puffs"))
        await msg.delete()
        await asyncio.sleep(2)
        await error.delete()
        return
    
    data = await state.get_data()
    await state.update_data(puffs=int(msg.text))
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("enter_strength"),
        reply_markup=strengths_kb()
    )

    await state.set_state(SellerAddProduct.strength)



@seller_router.callback_query(
    SellerAddProduct.strength,
    F.data.startswith("strength_")
)
async def add_strength_btn(cb: CallbackQuery, state: FSMContext):
    strength = cb.data.replace("strength_", "")
    await state.update_data(strength=strength)
    await state.set_state(SellerAddProduct.price)

    await cb.message.edit_text(
        _("enter_price"),
        reply_markup=cancel_kb()
    )

@seller_router.message(SellerAddProduct.strength)
async def add_strength_text(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        error = await msg.answer(_("invalid_strength"))
        await msg.delete()
        await asyncio.sleep(2)
        await error.delete()
        return

    data = await state.get_data()
    await state.update_data(strength=msg.text)
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("enter_price"),
        reply_markup=cancel_kb()
    )

    await state.set_state(SellerAddProduct.price)




@seller_router.message(SellerAddProduct.price)
async def add_price(msg: Message, state: FSMContext):
    if not msg.text.isdigit():
        error = await msg.answer(_("invalid_price"))
        await msg.delete()
        await asyncio.sleep(2)
        await error.delete()
        return

    data = await state.get_data()
    await state.update_data(price=int(msg.text))
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("send_photo"),
        reply_markup=cancel_kb()
    )

    await state.set_state(SellerAddProduct.photo)



def crop_to_square(image: Image.Image) -> Image.Image:
    w, h = image.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return image.crop((left, top, left + side, top + side))



@seller_router.message(SellerAddProduct.photo, F.photo)
async def add_photo(msg: Message, state: FSMContext):
    temp_msg = await msg.answer(_("second"))


    file_id = msg.photo[-1].file_id
    file = await msg.bot.get_file(file_id)
    file_bytes = await msg.bot.download_file(file.file_path)
    
    await state.update_data(
    photo_bytes=file_bytes.read(),
    tg_file_id=file_id)
    await asyncio.sleep(1)

    try:
        await msg.delete()
        await temp_msg.delete()
    except Exception:
        pass 

    data = await state.get_data()
    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("enter_flavors"),
        reply_markup=cancel_kb()
    )
    
    await state.set_state(SellerAddProduct.flavors)


def normalize_flavor(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()


@seller_router.message(SellerAddProduct.flavors)
async def add_flavors(msg: Message, state: FSMContext, session: AsyncSession):
    flavors = [f.strip().capitalize() for f in msg.text.splitlines() if f.strip()]
    await state.update_data(flavors=flavors)

    data = await state.get_data()

    city_id = data.get("city_id")
    if not city_id:
        await msg.answer("city error")
        await state.clear()
        return

    city = await session.get(City, city_id)
    if not city:
        await msg.answer("city error")
        await state.clear()
        return

    image = Image.open(BytesIO(data['photo_bytes'])).convert("RGB")
    square = crop_to_square(image)

    buffer = BytesIO()
    square.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    photo_file = BufferedInputFile(buffer.getvalue(), filename="preview.jpg")
    prosto_fl = _("prosto_flavors")
    lang = ctx_lang.get()
    city_name = city.name_lv if lang == "lv" else city.name_ru
    caption = (
        f"---{data['name']}---\n"
        f" 🏙 {city_name}\n"
        f" 🏷 {data['brand']}\n"
        f" 💨 {data['puffs']} тяг\n"
        f" 🔥 {data['strength']}\n"
        f" 💶 {data['price']}€\n\n"
        f" {prosto_fl}\n" + "\n".join(flavors)
    )

    await msg.bot.edit_message_media(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        media=InputMediaPhoto(media=photo_file, caption=caption),
        reply_markup=confirm_kb()
    )

    await msg.delete()
    await state.set_state(SellerAddProduct.confirm)
    await state.update_data(final_photo_bytes=buffer.getvalue())


@seller_router.callback_query(F.data == "confirm_add")
async def confirm_add(
    cb: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    seller: Seller,
    user: User
):
    data = await state.get_data()

    if not data or 'final_photo_bytes' not in data:
        await cb.answer(_("invalid_confirm."), show_alert=True)
        return

    city_id = data.get("city_id")
    if not city_id:
        await cb.message.answer(_("not_city"))
        await state.clear()
        return

    city_obj = await session.get(City, city_id)
    if not city_obj:
        await cb.message.answer(_("not_city"))
        await state.clear()
        return

    current_seller = seller
    if not current_seller and user.role == "super_admin":
        stmt = select(Seller).where(Seller.user_id == user.id)
        current_seller = await session.scalar(stmt)

        if not current_seller:
            current_seller = Seller(user_id=user.id)
            session.add(current_seller)
            await session.flush()

    if not current_seller:
        current_seller = Seller(user_id=user.id)
        session.add(current_seller)
        await session.flush()

    product = Product(
        name=data['name'],
        city_id=city_obj.id,
        seller_id=current_seller.id,
        price=Decimal(str(data['price'])),
        quantity_tyg=int(data['puffs']),
        strength_mg=int(data['strength']),
        brand=data['brand'],
        image_path=data["tg_file_id"],
        in_stock=True
    )

    session.add(product)
    await session.flush()

    for flavor_name in data.get("flavors", []):
        session.add(Flavor(name=flavor_name, product_id=product.id))

    await session.commit()
    await state.clear()

    try:
        await cb.message.answer(_("product_added", name=data['name']))
        await cb.message.answer(
            _("returned_to_seller_panel"),
            reply_markup=seller_panel_kb(),
            parse_mode="Markdown"
        )
        await cb.message.delete()
    except Exception:
        await cb.message.answer(_("error_maybe"))




@seller_router.callback_query(F.data == "seller_edit")
async def edit_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession, seller: Seller):
    if not seller:
        return await cb.answer(_("not_registered"), show_alert=True)
    
    kb = await edit_cities_kb(seller.id, session) 
    
    if not kb.inline_keyboard:
        return await cb.answer(_("not_products"), show_alert=True)
    
    try:
        await cb.message.delete()
    except Exception:
        pass

    await cb.message.answer(
        _("select_city_for_add"), 
        reply_markup=kb, 
        parse_mode="HTML"
    )

    await cb.answer()
    
    await state.set_state(SellerEditProduct.city)

@seller_router.callback_query(F.data.startswith("edit_city_"))
async def edit_choose_city(cb: CallbackQuery, state: FSMContext, session: AsyncSession, seller: Seller):
    city_id = int(cb.data.replace("edit_city_", ""))

    kb = await edit_products_kb(seller.id, city_id, session)
    
    await cb.message.edit_text(_("my_products_title"), reply_markup=kb, parse_mode="HTML")
    
    await state.update_data(city_id=city_id)
    await state.set_state(SellerEditProduct.product)

@seller_router.callback_query(F.data.startswith("edit_product_"))
async def choose_product(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    product_id = int(cb.data.replace("edit_product_", ""))
    await state.update_data(product_id=product_id)

    product = await session.get(Product, product_id)
    if not product:
        await cb.answer(_("not_product"), show_alert=True)
        return

    result = await session.execute(select(Flavor).where(Flavor.product_id == product_id))
    flavors = result.scalars().all()
    
    fl_text = ", ".join([f.name for f in flavors]) if flavors else _("status_not")
    status = _("status_in_stock") if product.in_stock else _("status_out_of_stock")
    
    caption = _("product_card_caption", 
                name=product.name, 
                brand=product.brand, 
                puffs=product.quantity_tyg, 
                strength=product.strength_mg, 
                price=product.price, 
                status=status, 
                flavors=fl_text)

    kb = edit_product_actions_kb(product.id, product.in_stock)

    await cb.message.delete()

    msg = await cb.message.answer_photo(
        photo=product.image_path,
        caption=caption,
        reply_markup=kb,
        parse_mode="HTML"
    )

    await state.update_data(bot_msg_id=msg.message_id)
    
    await cb.answer()

def get_product_caption(product, flavors: list) -> str:
    flavor_names = [f.name if hasattr(f, 'name') else f for f in flavors]
    fl_text = ", ".join(flavor_names) if flavor_names else "—"
    status = _("status_in_stock") if product.in_stock else _("status_out_of_stock")

    text = _("edit_menu_caption", 
            name=product.name, 
            brand=product.brand, 
            puffs=product.quantity_tyg, 
            strength=product.strength_mg, 
            price=product.price, 
            status=status, 
            flavors=fl_text)
    
    return text

@seller_router.callback_query(F.data.startswith("sel_act:edit:"))
async def seller_edit_field_start(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    
    field = parts[2] 
    product_id = int(parts[3])

    fields_map = {
        "name": "field_name",
        "brand": "field_brand",
        "puffs": "field_puffs",
        "strength": "field_strength",
        "price": "field_price"
    }

    label_key = fields_map.get(field, "field_default")
    translated_label = _(label_key)

    await state.update_data(
        edit_product_id=product_id, 
        edit_field=field, 
        bot_msg_id=cb.message.message_id
    )

    prompt_text = _("prompt_edit", field_name=translated_label)
    
    prompt = await cb.message.answer(prompt_text)
    
    await state.update_data(prompt_msg_id=prompt.message_id)
    await state.set_state(SellerEditProduct.waiting_edit_value)
    await cb.answer()
    


@seller_router.message(SellerEditProduct.waiting_edit_value)
async def seller_edit_field_save(msg: Message, state: FSMContext, session: AsyncSession, seller: Seller):
    data = await state.get_data()
    product = await session.get(Product, data['edit_product_id'])
    field = data['edit_field']
    
    try:
        val = msg.text.strip()
        if field == "name": product.name = val
        elif field == "brand": product.brand = val
        elif field == "puffs": product.quantity_tyg = int(val)
        elif field == "strength": product.strength_mg = int(val)
        elif field == "price": product.price = Decimal(val.replace(',', '.'))

    except Exception:
        return await msg.answer(_("error_format"))

    await msg.delete()
    try: await msg.bot.delete_message(msg.chat.id, data['prompt_msg_id'])
    except: pass

    await refresh_seller_card(msg, product, data['bot_msg_id'], session)
    await state.set_state(None)

async def refresh_seller_card(event, product, bot_msg_id, session):
    result = await session.execute(select(Flavor).where(Flavor.product_id == product.id))
    flavors = result.scalars().all()
    fl_text = ", ".join([f.name for f in flavors]) if flavors else _("status_not")
    status = _("status_in_stock") if product.in_stock else _("status_out_of_stock")


    caption = _("product_card_caption", 
                name=product.name, 
                brand=product.brand, 
                puffs=product.quantity_tyg, 
                strength=product.strength_mg, 
                price=product.price, 
                status=status, 
                flavors=fl_text)


    kb = edit_product_actions_kb(product.id, product.in_stock)
    
    try:
        await event.bot.edit_message_caption(
            chat_id=event.chat.id, message_id=bot_msg_id,
            caption=caption, reply_markup=kb, parse_mode="HTML"
        )
    except:
        await event.bot.send_photo(event.chat.id, photo=product.image_path, caption=caption, reply_markup=kb)

@seller_router.callback_query(F.data.startswith("sel_act:photo:"))
async def seller_edit_photo_start(cb: CallbackQuery, state: FSMContext):
    product_id = int(cb.data.split(":")[2])

    await state.update_data(
        edit_product_id=product_id,
        bot_msg_id=cb.message.message_id
    )

    prompt = await cb.message.answer(_("send_new_photo"))
    await state.update_data(prompt_msg_id=prompt.message_id)

    await state.set_state(SellerEditProduct.waiting_edit_photo)
    await cb.answer()

@seller_router.message(SellerEditProduct.waiting_edit_photo, F.photo)
async def seller_edit_photo_save(
    msg: Message,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    product = await session.get(Product, data["edit_product_id"])

    wait_msg = await msg.answer(_("second"))

    tg_file = await msg.bot.get_file(msg.photo[-1].file_id)
    downloaded = await msg.bot.download_file(tg_file.file_path)
    image_bytes = downloaded.read()

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    square = crop_to_square(image)

    buffer = BytesIO()
    square.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    sent = await msg.bot.send_photo(
        chat_id=msg.chat.id,
        photo=BufferedInputFile(buffer.getvalue(), "photo")
    )

    product.image_path = sent.photo[-1].file_id

    for mid in (
        msg.message_id,
        sent.message_id,
        data.get("prompt_msg_id"),
        data.get("bot_msg_id"),
        wait_msg.message_id
    ):
        try:
            await msg.bot.delete_message(msg.chat.id, mid)
        except:
            pass

    await refresh_seller_card(
        msg,
        product,
        bot_msg_id=None,
        session=session
    )

    await state.clear()


@seller_router.callback_query(F.data.startswith("sel_act:toggle:"))
async def seller_toggle_stock(cb: CallbackQuery, session: AsyncSession):
    product_id = int(cb.data.split(":")[2])
    product = await session.get(Product, product_id)
    
    product.in_stock = not product.in_stock
    
    await refresh_seller_card(cb.message, product, cb.message.message_id, session)
    await cb.answer(_("status_edit"))


def normalize_flavor(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()

@seller_router.callback_query(F.data.startswith("sel_act:add_fl:"))
async def seller_add_flavor_start(cb: CallbackQuery, state: FSMContext):
    product_id = int(cb.data.split(":")[2])

    await state.update_data(
        product_id=product_id,
        product_msg_id=cb.message.message_id
    )

    prompt = await cb.message.answer(_("edt_new_flavors_add"))
    await state.update_data(prompt_msg_id=prompt.message_id)

    await state.set_state(SellerEditProduct.add_flavors)
    await cb.answer()

@seller_router.message(SellerEditProduct.add_flavors, F.text)
async def seller_add_flavor_save(
    msg: Message,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    product = await session.get(Product, data["product_id"])

    for line in msg.text.splitlines():
        name = normalize_flavor(line)
        if not name:
            continue

        stmt = select(Flavor).where(
            Flavor.product_id == product.id,
            Flavor.name == name
        )
        exists = await session.scalar(stmt)
        if not exists:
            session.add(Flavor(name=name, product_id=product.id))

    await refresh_seller_card(
        msg,
        product,
        bot_msg_id=data["product_msg_id"],
        session=session
    )

    for mid in (msg.message_id, data["prompt_msg_id"]):
        try:
            await msg.bot.delete_message(msg.chat.id, mid)
        except:
            pass

    await state.clear()

@seller_router.callback_query(F.data.startswith("sel_act:rem_fl:"))
async def seller_remove_flavor_start(cb: CallbackQuery, state: FSMContext):
    product_id = int(cb.data.split(":")[2])

    await state.update_data(
        product_id=product_id,
        product_msg_id=cb.message.message_id
    )

    prompt = await cb.message.answer(_("edt_new_flavors_del"))
    await state.update_data(prompt_msg_id=prompt.message_id)

    await state.set_state(SellerEditProduct.remove_flavors)
    await cb.answer()

    
@seller_router.message(SellerEditProduct.remove_flavors, F.text)
async def seller_remove_flavor_save(
    msg: Message,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    product = await session.get(Product, data["product_id"])

    for line in msg.text.splitlines():
        name = normalize_flavor(line)
        if not name:
            continue

        stmt = select(Flavor).where(
            Flavor.product_id == product.id,
            Flavor.name == name
        )
        flavor = await session.scalar(stmt)
        if flavor:
            await session.delete(flavor)

    await refresh_seller_card(
        msg,
        product,
        bot_msg_id=data["product_msg_id"],
        session=session
    )

    for mid in (msg.message_id, data["prompt_msg_id"]):
        try:
            await msg.bot.delete_message(msg.chat.id, mid)
        except:
            pass

    await state.clear()

@seller_router.callback_query(F.data.startswith("sel_act:delete:"))
async def admin_delete_confirm(cb: CallbackQuery, session: AsyncSession):
    product_id = int(cb.data.split(":")[2])
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("confirm_delete_btn"), callback_data=f"sel_act:confirm_del:{product_id}")],
        [InlineKeyboardButton(text=_("cancel_btn"), callback_data=f"edit_product_{product_id}")]
    ])
    
    await cb.message.edit_caption(
        caption=_("confirm_delete_text"),
        reply_markup=kb,
        parse_mode="HTML"
    )

@seller_router.callback_query(F.data.startswith("sel_act:confirm_del:"))
async def seller_delete_product_confirm(cb: CallbackQuery, session: AsyncSession, user: User):
    product_id = int(cb.data.split(":")[2])
    product = await session.get(Product, product_id)
    
    if not product:
        return await cb.answer(_("error_delete"))

    city_id = product.city_id 
    
    await session.execute(delete(Flavor).where(Flavor.product_id == product_id))
    await session.delete(product)
    await session.commit()
    
    await cb.answer(_("product_deleted"), show_alert=True)

    result = await session.execute(
        select(Product).where(
            Product.seller_id == user.id, 
            Product.city_id == city_id
        ).limit(1)
    )
    has_remaining = result.scalar() is not None

    if has_remaining:
        kb = await edit_products_kb(seller_id=user.id, city_id=city_id, session=session)
        
        await cb.message.answer(
            text=_("my_products_title"),
            reply_markup=kb,
            parse_mode="HTML"
        )
        await cb.message.delete()
    else:
        await cb.message.answer(
            _("seller_panel"),
            reply_markup=seller_panel_kb()
        )
        await cb.message.delete()



def format_buyer(user) -> str:
    if user.username:
        return f"@{user.username}"

    return f"<a href='tg://user?id={user.tg_id}'>ID:{user.tg_id}</a>"

def format_seller(user) -> str:
    if user.username:
        return f"@{user.username}"

    if user.full_name and user.full_name.strip():
        return f"ID:{user.tg_id} | {user.full_name}"

    return f"ID:{user.tg_id}"

@seller_router.callback_query(F.data == "seller_orders")
async def seller_orders(cb: CallbackQuery, session: AsyncSession, seller: Seller):
    stmt = (
        select(Order)
        .where(
            Order.seller_id == seller.id,
            Order.status == "pending" 
        )
        .order_by(Order.created_at.desc())
        .options(selectinload(Order.product))
    )

    orders = (await session.execute(stmt)).scalars().all()

    if not orders:
        await cb.answer(_("not_orders"), show_alert=True)
        return

    kb = InlineKeyboardBuilder()

    for order in orders:
        date_str = order.created_at.strftime("%d.%m %H:%M")
        
        btn_text = f"{date_str} | {order.product.name}"
        
        kb.button(
            text=btn_text,
            callback_data=f"order:view:{order.id}"
        )

    kb.button(text=_("back"), callback_data="seller_panel")
    kb.adjust(1)

    await cb.message.edit_text(
        _("waiting_orders_choose"),
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await cb.answer()

@seller_router.callback_query(F.data.startswith("order:view:"))
async def view_order(cb: CallbackQuery, session: AsyncSession):
    order_id = int(cb.data.split(":")[-1])

    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.user), 
            selectinload(Order.product),
            selectinload(Order.flavors).selectinload(OrderFlavor.flavor)
        )
    )
    order = (await session.execute(stmt)).scalar_one_or_none()

    if not order:
        await cb.answer(_("not_order"), show_alert=True)
        return

    flavor_items = []
    for of in order.flavors:
        item = _("flavor_qty_format", name=of.flavor.name, qty=of.quantity)
        flavor_items.append(item)
    
    flavors = ", ".join(flavor_items) or _("no_flavors")

    user_link = format_buyer(order.user)
    
    status_localized = _(f"status_{order.status}")

    text = (
        f"{_('order_view_title', id=order.id)}\n"           # 📦 Заказ №...
        f"{_('order_buyer', buyer=user_link)}\n"            # 👤 Покупатель...
        f"{_('order_product', name=order.product.name)}\n"  # 🚬 Товар...
        f"{_('order_puffs', puffs=order.quantity_tyg)}\n"   # 💨 Тяги... 
        f"{_('order_view_flavors', flavors=flavors)}\n"     # 🧪 Вкусы...
        f"{_('order_price', price=order.total_price)}\n\n"  # 💶 Сумма...
        f"📌 {_('status_label')}: <b>{status_localized}</b>" # 📌 Статус...
    )

    kb = order_card_kb(order) 
    
    if kb is None:
        builder = InlineKeyboardBuilder()
        builder.button(text=_("prosto_back"), callback_data="seller_orders")
        kb = builder.as_markup()
    else:
        pass 

    await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await cb.answer()



async def notify_seller(bot: Bot, session: AsyncSession, order_id: int):

    stmt = select(Order).where(Order.id == order_id).options(
        selectinload(Order.seller).selectinload(Seller.user),
        selectinload(Order.user),
        selectinload(Order.product)
    )
    order = (await session.execute(stmt)).scalar_one()
    

    seller_user = order.seller.user
    lang = seller_user.language or "ru"
    
  
    token = ctx_lang.set(lang)
    
    try:
        buyer = order.user
        buyer_ref = f"@{buyer.username}" if buyer.username else buyer.full_name
        
    
        text = (
            f"<b>{_('order_notification', id=order.id)}</b>\n\n"
            f"{_('order_buyer', buyer=buyer_ref)}\n"
            f"{_('order_product', name=order.product.name)}\n"
            f"{_('order_price', price=order.total_price)}\n\n"
            f"<i>{_('order_notify_footer')}</i>"
        )
        
        await bot.send_message(seller_user.tg_id, text, parse_mode="HTML")
    finally:
       
        ctx_lang.reset(token)



async def generate_order_number(session: AsyncSession) -> int:
    result = await session.execute(
        select(Order.order_number).where(Order.order_number != None).order_by(desc(Order.order_number)).limit(1)
    )
    last_number = result.scalar() or 0
    return last_number + 1



async def check_remaining_orders(call: CallbackQuery, session: AsyncSession, seller: Seller):
    stmt = select(Order).where(
        Order.seller_id == seller.id,
        Order.status == "pending"
    ).order_by(Order.created_at.desc()).options(selectinload(Order.product))
    
    orders = (await session.execute(stmt)).scalars().all()
    
    if not orders:

        await call.message.edit_text(
            _("no_orders_left"), 
            reply_markup=seller_panel_kb() 
        )
    else:
        kb = InlineKeyboardBuilder()
        for o in orders:
            time_str = o.created_at.strftime("%d.%m %H:%M")
            kb.button(text=f"🕒 {time_str} | {o.product.name}", callback_data=f"order:view:{o.id}")
        kb.button(text=_("prosto_back"), callback_data="seller_panel")
        kb.adjust(1)
        await call.message.edit_text(_("waiting_orders_choose"), reply_markup=kb.as_markup())


@seller_router.callback_query(F.data.startswith("order:cancel:"))
async def cancel_order(call: CallbackQuery, session: AsyncSession, seller: Seller):
    order_id = int(call.data.split(":")[-1])
    order = await session.get(Order, order_id)
    if order.status != "pending":
        return await call.answer(_("order_already_processed"), show_alert=True)
    
    if order:
        order.status = "cancelled"
        await session.commit()
        await call.answer(_("order_cancelled_well", id=order.id))
    
    await check_remaining_orders(call, session, seller)


@seller_router.callback_query(F.data.startswith("order:confirm:"))
async def confirm_order(call: CallbackQuery, session: AsyncSession, seller: Seller):
    order_id = int(call.data.split(":")[-1])
    order = await session.get(Order, order_id)

    if not order:
        return await call.answer(_("order_error"), show_alert=True)

    if order.status != "pending":
        return await call.answer(_("order_already_processed"), show_alert=True)

    order.status = "confirmed"
    await session.commit()

    await call.answer(_("order_complete_well", order_number=order.id))
    await check_remaining_orders(call, session, seller)


@seller_router.callback_query(F.data == "seller_stats")
async def seller_stats(cb: CallbackQuery, session: AsyncSession, seller: Seller | None):
    if not seller:
        return await cb.answer(_("error_seller_profile"), show_alert=True)
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_stmt = select(
        func.count(Order.id),
        func.coalesce(func.sum(Order.total_price), 0)
    ).where(
        Order.seller_id == seller.id,
        Order.status.in_(["confirmed", "completed"])
    )

    total_count, total_sum = (await session.execute(total_stmt)).one()

    month_stmt = select(
        func.count(Order.id),
        func.coalesce(func.sum(Order.total_price), 0)
    ).where(
        Order.seller_id == seller.id,
        Order.status.in_(["confirmed", "completed"]),
        Order.created_at >= month_start
    )

    month_count, month_sum = (await session.execute(month_stmt)).one()

    top_product_stmt = (
        select(
            Product.name,
            func.sum(Order.quantity_tyg).label("total_qty")
        )
        .join(Order, Order.product_id == Product.id)
        .where(
            Order.seller_id == seller.id,
            Order.status.in_(["confirmed", "completed"])
        )
        .group_by(Product.id)
        .order_by(func.sum(Order.quantity_tyg).desc())
        .limit(1)
    )

    top_product = (await session.execute(top_product_stmt)).first()

    top_product_name = top_product[0] if top_product else "—"

    text = (
        f"{_('stats_title')}\n\n"
        "━━━━━━━━━━━━━━\n\n"
        f"{_('stats_all_time', count=total_count, sum=total_sum)}\n"
        f"{_('stats_month', count=month_count, sum=month_sum)}\n"
        f"{_('stats_top_product', name=top_product_name)}\n\n"
        "━━━━━━━━━━━━━━"
    )

    kb = InlineKeyboardBuilder()
    kb.button(text=_("back_to_stat"), callback_data="seller_panel") 

    kb.adjust(1)

    await cb.message.answer(
        text,
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await cb.answer()