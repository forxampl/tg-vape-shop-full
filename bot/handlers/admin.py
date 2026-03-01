from aiogram import Router, F
from sqlalchemy import select, update, func
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Product, User, Seller, City, Flavor, Order, Feedback, OrderFlavor
from bot.states.admin import AdminStates, AdminAddProduct, AdminFeedback
from bot.keyboards.admin import admin_panel_kb, admin_cities_kb, admin_cancel_kb, confirm_broadcast_kb, admin_members_kb, admin_products_kb, get_product_edit_kb, admin_sellers_kb, admin_products_management_kb, admin_cities_kb, admin_brands_kb, admin_cities_select_kb, admin_feedback_actions_kb, admin_feedbacks_list_kb, admin_order_card_kb, confirm_city_translation_kb
from bot.keyboards.seller import strengths_kb
from sqlalchemy.orm import selectinload
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from decimal import Decimal
from io import BytesIO
from aiogram.filters import BaseFilter
from PIL import Image
import asyncio
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from bot.middlewares.translator import _, ctx_lang
from aiogram.utils.keyboard import InlineKeyboardBuilder
from zoneinfo import ZoneInfo
from bot.main import bot
from contextlib import contextmanager
from bot.middlewares.city_translator import translate_city
import re

@contextmanager
def use_lang(lang: str):
    token = ctx_lang.set(lang)
    try:
        yield
    finally:
        ctx_lang.reset(token)

admin_router = Router()

FLAG_TO_ROLE = {
    "-S": "seller",
    "-A": "admin",
    "-U": "user"
}

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message, user: User) -> bool:
        return user.role in ["admin", "super_admin"]

admin_router.message.filter(IsAdmin())
admin_router.callback_query.filter(IsAdmin())

@admin_router.message(F.text == "/admin")
async def admin_start(message: Message, state: FSMContext, user: User): 
    await message.answer(
        _("admin_panel_title"),
        reply_markup=admin_panel_kb(),  
        parse_mode="HTML"
    )




@admin_router.callback_query(F.data == "admin_back")
async def admin_back(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(_("admin_panel_title"), reply_markup=admin_panel_kb())

@admin_router.callback_query(F.data == "admin_cities")
async def admin_cities_menu(cb: CallbackQuery):
    await cb.message.edit_text(
        _("manage_cities"), 
        reply_markup=admin_cities_kb(), 
        parse_mode="HTML"
    )
    await cb.answer()



def is_russian(text: str) -> bool:
    return bool(re.search('[а-яА-Я]', text))

@admin_router.callback_query(F.data == "add_city_start")
async def add_city_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_city_add)
    await cb.message.edit_text(
        _("enter_city_name"),
        reply_markup=admin_cancel_kb(),
        parse_mode="HTML"
    )
    await cb.answer()

@admin_router.message(AdminStates.waiting_city_add)
async def proc_add_city(message: Message, state: FSMContext, session: AsyncSession):
    name = message.text.strip()
    
    if is_russian(name):
        orig_lang = 'ru'
        name_ru = name
        name_lv = translate_city(name, 'ru', 'lv')
    else:
        orig_lang = 'lv'
        name_lv = name
        name_ru = translate_city(name, 'lv', 'ru')

    result = await session.execute(
        select(City).where(
            (City.name_ru.ilike(name_ru)) | 
            (City.name_lv.ilike(name_lv))
        )
    )
    if result.scalars().first():
        return await message.answer(_("city_exists"))

    await state.update_data(orig_lang=orig_lang, temp_ru=name_ru, temp_lv=name_lv)
    await state.set_state(AdminStates.confirm_city_translation)

    await message.answer(
        _("city_confirm_text", ru=name_ru, lv=name_lv),
        reply_markup=confirm_city_translation_kb(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "city_confirm_yes")
async def city_confirm_yes(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    
    new_city = City(
        name_ru=data.get("temp_ru"), 
        name_lv=data.get("temp_lv")
    )
    session.add(new_city)
    await session.commit()

    display_name = data.get("temp_lv") if ctx_lang.get() == "lv" else data.get("temp_ru")
    await cb.message.edit_text(_("city_added", city_name=display_name))
    await state.clear()

@admin_router.callback_query(F.data == "city_confirm_no")
async def city_confirm_no(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    orig_lang = data.get("orig_lang")
    
    await state.set_state(AdminStates.manual_city_translation)
    
    prompt_key = "city_manual_lv" if orig_lang == 'ru' else "city_manual_ru"
    await cb.message.edit_text(_(prompt_key))

@admin_router.message(AdminStates.manual_city_translation)
async def manual_translation_proc(message: Message, state: FSMContext, session: AsyncSession):
    new_input = message.text.strip()
    data = await state.get_data()
    orig_lang = data.get("orig_lang")
    
    if orig_lang == 'ru':
        name_ru = data.get("temp_ru")
        name_lv = new_input
    else:
        name_lv = data.get("temp_lv")
        name_ru = new_input

    if not name_ru: name_ru = new_input
    if not name_lv: name_lv = new_input

    new_city = City(name_ru=name_ru, name_lv=name_lv)
    session.add(new_city)
    await session.commit()

    display_name = name_lv if ctx_lang.get() == "lv" else name_ru
    await message.answer(_("city_added", city_name=display_name))
    await state.clear()


@admin_router.callback_query(F.data == "del_city_start")
async def del_city_start(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.set_state(AdminStates.waiting_city_del)
    result = await session.execute(select(City))
    cities = result.scalars().all()
    if not cities:
        return await cb.answer("Нет городов для удаления", show_alert=True)
    
    city_names = "\n".join(
        city.name_lv if ctx_lang.get() == "lv" else city.name_ru
        for city in cities
    )
    await cb.message.edit_text(
        _("delete_city_prompt", city_names=city_names),
        reply_markup=admin_cancel_kb(), 
        parse_mode="HTML"
    )
    await cb.answer()

@admin_router.message(AdminStates.waiting_city_del)
async def process_city_delete_name(message: Message, state: FSMContext, session: AsyncSession):
    city_name_input = message.text.strip()
    if not city_name_input:
        return await message.answer(_("empty_input_error") or "Введите название города.")

    result = await session.execute(
        select(City).where(
            (City.name_ru.ilike(city_name_input)) |
            (City.name_lv.ilike(city_name_input))
        )
    )
    city = result.scalar_one_or_none()

    if not city:
        return await message.answer(
            _("city_not_found", city_name=city_name_input)
        )

    await state.update_data(city_id_to_delete=city.id)

    display_name = city.name_lv if ctx_lang.get() == "lv" else city.name_ru

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=_("confirm_delete_city_yes"),
                callback_data=f"confirm_del_city:{city.id}"
            ),
            InlineKeyboardButton(
                text=_("confirm_delete_city_no"),
                callback_data="cancel_del_city"
            )
        ]
    ])

    await message.answer(
        _("confirm_delete_city_text", city_name=display_name, city_id=city.id),
        reply_markup=kb,
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("confirm_del_city:"))
async def confirm_delete_city(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    city_id = int(cb.data.split(":")[1])

    city = await session.get(City, city_id)
    if not city:
        await cb.answer(_("city_not_found", city_name=""), show_alert=True)
        await state.clear()
        return

    orders_count = await session.scalar(
        select(func.count()).select_from(Order).where(Order.city_id == city.id)
    )

    display_name = city.name_lv if ctx_lang.get() == "lv" else city.name_ru

    if orders_count > 0:
        await cb.message.edit_text(
            _("city_delete_blocked_orders", 
              city_name=display_name, 
              orders_count=orders_count),
            reply_markup=None,
            parse_mode="HTML"
        )
        await state.clear()
        return

    try:
        await session.delete(city)
        await session.commit()

        await cb.message.edit_text(
            _("city_delete_success", city_name=display_name),
            reply_markup=admin_cities_kb(),
            parse_mode="HTML"
        )
        await cb.answer(_("city_deleted"))

    except Exception as e:
        await session.rollback()
        await cb.message.edit_text(
            f"❌ {_('city_delete_error') or 'Ошибка при удалении'}: {str(e)}",
            parse_mode="HTML"
        )
        await cb.answer(_("error"), show_alert=True)

    await state.clear()


@admin_router.callback_query(F.data == "cancel_del_city")
async def cancel_delete_city(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        _("city_delete_cancelled"),
        reply_markup=admin_cities_kb(),
        parse_mode="HTML"
    )
    await cb.answer(_("action_cancelled"))


async def get_members_text(session: AsyncSession):
    result = await session.execute(select(User))
    users = result.scalars().all()

    super_admins = []
    admins = []
    sellers = []
    a = _("not_name")
    for u in users:

        link = f"@{u.username}" if u.username else f"`{u.tg_id}`"
        user_str = f"👤 {u.username or a} | {link}"

        if u.role == "super_admin":
            super_admins.append(user_str)
        elif u.role == "admin":
            admins.append(user_str)
        elif u.role == "seller":
            sellers.append(user_str)


    text = _("members_list_title")
    
    text += _("role_super_admin") + ("\n".join(super_admins) if super_admins else "—") + "\n\n"
    text += _("role_admins") + ("\n".join(admins) if admins else "—") + "\n\n"
    text += _("role_sellers") + ("\n".join(sellers) if sellers else "—")
    
    return text


@admin_router.callback_query(F.data == "admin_roles")
async def admin_members_list(cb: CallbackQuery, session: AsyncSession):
    text = await get_members_text(session)
    await cb.message.edit_text(text, reply_markup=admin_members_kb(), parse_mode="HTML")
    await cb.answer()


@admin_router.callback_query(F.data == "admin_roles_start")
async def admin_roles_edit(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.change_role)
    text = _("change_role_instr")
    await cb.message.edit_text(text, reply_markup=admin_cancel_kb(), parse_mode="HTML")
    await cb.answer()



@admin_router.message(AdminStates.change_role)
async def process_role_change(message: Message, state: FSMContext, session: AsyncSession, bot):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            return await message.answer("Формат: [ID] [ФЛАГ] (например: 12345 -S)")
        
        tg_id_str, flag = parts[0], parts[1].upper()
        if flag not in FLAG_TO_ROLE:
            return await message.answer("Неверный флаг! Используйте -S, -A или -U")

        tg_id = int(tg_id_str)
        

        result = await session.execute(select(User).where(User.tg_id == tg_id))
        target_user = result.scalars().first()
        
        if not target_user:
            return await message.answer("Пользователь не найден.")
        
        if target_user.role == 'super_admin':
            return await message.answer("Нельзя менять роль супер-админу.")

        old_role = target_user.role
        new_role = FLAG_TO_ROLE[flag]
        

        target_user.role = new_role
        if new_role == "seller":
            seller_profile = await session.scalar(select(Seller).where(Seller.user_id == target_user.id))
            
            if seller_profile:
   
                seller_profile.is_active = True
            else:
     
                new_seller = Seller(user_id=target_user.id, is_active=True)
                session.add(new_seller)
                

        elif old_role == "seller" and new_role != "seller":

            seller_profile = await session.scalar(select(Seller).where(Seller.user_id == target_user.id))
            if seller_profile:
                seller_profile.is_active = False
                

                await session.execute(
                    update(Product).where(Product.seller_id == seller_profile.id).values(in_stock=False)
                )

        await session.commit()

        try:
            await bot.send_message(target_user.tg_id, f"Ваша роль была изменена на: <b>{new_role.upper()}</b>", parse_mode="HTML")
        except:
            pass

        await state.clear()
        new_list_text = await get_members_text(session)
        await message.answer(
            f"✅ Роль пользователя {tg_id} изменена на {new_role}.\nПрофиль продавца: {'активирован' if new_role == 'seller' else 'деактивирован'}.\n\n" + new_list_text,
            reply_markup=admin_members_kb(),
            parse_mode="HTML"
        )

    except Exception as e:
        await session.rollback()
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode=None)


@admin_router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_broadcast_text)
    
    await cb.message.edit_text(
        _("broadcast_prep"),
        reply_markup=admin_cancel_kb(),
        parse_mode="HTML"
    )
    await cb.answer()


@admin_router.message(AdminStates.waiting_broadcast_text)
async def broadcast_preview(message: Message, state: FSMContext):
    broadcast_text = message.text
    await state.update_data(broadcast_text=broadcast_text)
    
    await message.answer(
        _("broadcast_preview",text=broadcast_text),
        reply_markup=confirm_broadcast_kb(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "broadcast_confirm_send")
async def start_broadcast(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    text = data.get("broadcast_text")

    if not text:
        await cb.answer("Текст рассылки не найден", show_alert=True)
        return

    result = await session.execute(
        select(User.tg_id).where(User.broadcast_disabled == False)
    )
    users = result.scalars().all()

    total_users = len(users)

    await cb.message.edit_text(
        _("broadcast_run", count_users=total_users),
        parse_mode="HTML"
    )

    sent_count = 0
    blocked_count = 0
    error_count = 0

    for user_id in users:
        try:
            await cb.bot.send_message(user_id, text)
            sent_count += 1

            if sent_count % 20 == 0:
                await asyncio.sleep(0.5)

        except TelegramForbiddenError:
            blocked_count += 1

        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await cb.bot.send_message(user_id, text)
                sent_count += 1
            except:
                error_count += 1

        except Exception:
            error_count += 1

    await cb.message.answer(
        _("broadcast_finished",
          count=sent_count,
          blocked=blocked_count,
          errors=error_count
        ),
        parse_mode="HTML"
    )

    await state.clear()


@admin_router.callback_query(F.data == "admin_edit")
async def admin_edit_menu(cb: CallbackQuery):
    await cb.message.edit_text(
        _("product_manage"),
        reply_markup=admin_products_management_kb(),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data == "admin_edit_products")
async def select_seller(cb: CallbackQuery, session: AsyncSession):
    result = await session.execute(
        select(Seller)
        .options(selectinload(Seller.user))
        .where(Seller.products.any())
    )
    sellers = result.scalars().all()

    if not sellers:
        await cb.answer(
            _("sellers_not_found"), 
            show_alert=True
        )
        return

    await cb.message.edit_text(
        _("choose_seller"),
        reply_markup=admin_sellers_kb(sellers)  
    )


@admin_router.callback_query(F.data.startswith("edt_sel:"))
async def select_product_for_edit(cb: CallbackQuery, session: AsyncSession, manual_id: int = None):
    seller_id = manual_id if manual_id is not None else int(cb.data.split(":")[1])
    

    result = await session.execute(
        select(Seller).options(selectinload(Seller.user)).where(Seller.id == seller_id)
    )
    seller_obj = result.scalars().first()

    if not seller_obj:
        return await cb.answer(_("sellers_not_found_error"))

    username = f"@{seller_obj.user.username}" if seller_obj.user.username else seller_obj.user.full_name
    

    products_res = await session.execute(
        select(Product).where(Product.seller_id == seller_id)
    )
    products = products_res.scalars().all()

    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"📦 {p.name} | {p.brand}", callback_data=f"edt_prod:{p.id}")])
    
    buttons.append([InlineKeyboardButton(text=_("back_to_sellers_btn"), callback_data="admin_edit")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    text = _("edit_products_seller", username=username)
    
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=kb, parse_mode="HTML")

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

@admin_router.callback_query(F.data.startswith("edt_prod:"))
async def show_product_card(cb: CallbackQuery, session: AsyncSession):
    product_id = int(cb.data.split(":")[1])

    product = await session.get(Product, product_id)
    result = await session.execute(select(Flavor).where(Flavor.product_id == product_id))
    flavors = result.scalars().all()

    caption = get_product_caption(product, flavors)

    kb = get_product_edit_kb(product)

    try:
        await cb.message.edit_media(
            media=InputMediaPhoto(
                media=product.image_path, 
                caption=caption,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    except:
        await cb.message.delete()
        await cb.message.answer_photo(
            photo=product.image_path,  
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML"
        )



@admin_router.callback_query(F.data.startswith("adm_act:edit:"))
async def admin_edit_field_start(cb: CallbackQuery, state: FSMContext):
    parts = cb.data.split(":")
    product_id = int(parts[3])
    field = parts[2] 
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
    prompt = await cb.message.answer(
    prompt_text,
    parse_mode="HTML"
    )  


    await state.update_data(prompt_msg_id=prompt.message_id)
    await state.set_state(AdminStates.waiting_edit_value)
    await cb.answer()

@admin_router.message(AdminStates.waiting_edit_value)
async def admin_edit_field_save(msg: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    product_id = data['edit_product_id']
    field = data['edit_field']
    
    product = await session.get(Product, product_id)
    if not product:
        return await msg.answer(_("product_not_found_error"))

    new_val = msg.text.strip()
    
    try:
        if field == "name": product.name = new_val
        elif field == "brand": product.brand = new_val
        elif field == "puffs": product.quantity_tyg = int(new_val)
        elif field == "strength": product.strength_mg = int(new_val)
        elif field == "price": product.price = Decimal(new_val)
        
    except ValueError:
        await msg.delete()
        return 

    await msg.delete() 
    try:
        await msg.bot.delete_message(msg.chat.id, data['prompt_msg_id']) 
    except: pass


    await refresh_admin_product_card(msg, product, data['bot_msg_id'], session)
    await state.clear()

async def refresh_admin_product_card(event, product, bot_msg_id, session):
    result = await session.execute(select(Flavor).where(Flavor.product_id == product.id))
    flavors = [f.name for f in result.scalars().all()]
    
    caption = get_product_caption(product, flavors)

    kb = get_product_edit_kb(product) 

    try:
        await event.bot.edit_message_caption(
            chat_id=event.chat.id,
            message_id=bot_msg_id,
            caption=caption,
            reply_markup=kb,
            parse_mode="HTML"
        )
    except:
        await event.bot.send_photo(
            chat_id=event.chat.id,
            photo=product.image_path,
            caption=caption,
            reply_markup=kb
        )



@admin_router.callback_query(F.data.startswith("adm_act:photo:"))
async def edit_photo_start(cb: CallbackQuery, state: FSMContext):
    product_id = int(cb.data.split(":")[2])
    
    await state.update_data(
        edit_product_id=product_id, 
        bot_msg_id=cb.message.message_id
    )
    
    prompt_msg = await cb.message.answer(_("send_new_photo"))
    await state.update_data(prompt_msg_id=prompt_msg.message_id)
    
    await state.set_state(AdminStates.waiting_edit_photo)
    await cb.answer()


def crop_to_square(image: Image.Image) -> Image.Image:
    w, h = image.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return image.crop((left, top, left + side, top + side))

async def send_new_admin_card(event, product, session):
    result = await session.execute(select(Flavor).where(Flavor.product_id == product.id))
    flavors = [f.name for f in result.scalars().all()]
    
    caption = get_product_caption(product, flavors)

    kb = get_product_edit_kb(product)
    await event.bot.send_photo(
        chat_id=event.chat.id,
        photo=product.image_path,  
        caption=caption,
        reply_markup=kb,
        parse_mode="HTML"
    )

@admin_router.message(AdminStates.waiting_edit_photo, F.photo)
async def edit_photo_save(msg: Message, state: FSMContext, session: AsyncSession):
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
        photo=BufferedInputFile(buffer.getvalue(), "product.jpg")
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

    await send_new_admin_card(msg, product, session)

    await state.clear()


@admin_router.callback_query(F.data.startswith("adm_act:toggle_stock:"))
async def admin_toggle_stock(cb: CallbackQuery, session: AsyncSession):
    p_id = int(cb.data.split(":")[2])
    product = await session.get(Product, p_id)

    if not product:
        return await cb.answer(_("product_not_found"), show_alert=True)

    product.in_stock = not product.in_stock
    await session.commit()  

    res = await session.execute(
        select(Flavor).where(Flavor.product_id == p_id)
    )
    flavors = [f.name for f in res.scalars().all()]

    caption = get_product_caption(product, flavors)

    await cb.message.edit_caption(
        caption=caption,
        reply_markup=get_product_edit_kb(product),
        parse_mode="HTML"
    )
    await cb.answer(_("update_status"))



@admin_router.callback_query(F.data.startswith("adm_act:delete_prod:"))
async def admin_delete_confirm(cb: CallbackQuery):
    p_id = int(cb.data.split(":")[2])
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("confirm_delete_btn"), callback_data=f"admin_confirm_del:{p_id}")],
        [InlineKeyboardButton(text=_("cansel_delete_btn"), callback_data=f"edt_prod:{p_id}")]
    ])
    
    await cb.message.edit_caption(
        caption=_("confirm_delete_text"),
        reply_markup=kb,
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("admin_confirm_del:"))
async def admin_delete_final(cb: CallbackQuery, session: AsyncSession):
    p_id = int(cb.data.split(":")[1])
    product = await session.get(Product, p_id)
    
    if not product:
        return await cb.answer(_("product_not_found"))
        
    s_id = product.seller_id
        
    await session.delete(product)

    await cb.answer(_("product_deleted"), show_alert=True)


    res_products = await session.execute(
        select(Product).where(Product.seller_id == s_id)
    )
    remaining_products = res_products.scalars().all()

    if remaining_products:

        await cb.message.answer(
            _("product_deleted_seller_list"),
            reply_markup=admin_products_kb(remaining_products, s_id) 
        )
    else:
        res_sellers = await session.execute(
            select(Seller).options(selectinload(Seller.user)).where(Seller.products.any())
        )
        remaining_sellers = res_sellers.scalars().all()

        if remaining_sellers:
            await cb.message.answer(
                _("not_products_seller"),
                reply_markup=admin_sellers_kb(remaining_sellers)
            )
        else:
            await cb.message.answer(_("empty_products_list"),
                reply_markup=admin_panel_kb() 
            )

    try:
        await cb.message.delete()
    except Exception as e:
        print("error_delete_msg", e)


def normalize_flavor(name: str) -> str:
    name = name.strip()
    if not name:
        return ""
    return name[:1].upper() + name[1:].lower()

@admin_router.callback_query(F.data.startswith("adm_act:add_flavor:"))
async def admin_add_flavor_start(cb: CallbackQuery, state: FSMContext):
    p_id = int(cb.data.split(":")[2])
    await state.update_data(product_msg_id=cb.message.message_id, product_id=p_id)
    
    await state.set_state(AdminStates.waiting_add_flavors)
    prompt_msg = await cb.message.answer(_("edt_new_flavors_add"))
    await state.update_data(prompt_msg_id=prompt_msg.message_id)
    await cb.answer()

@admin_router.message(AdminStates.waiting_add_flavors, F.text)
async def admin_add_flavor_save(msg: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    product = await session.get(Product, data['product_id'])
    
    flavors_to_add = msg.text.splitlines()
    for f_name in flavors_to_add:
        f_name = f_name.strip().capitalize() 
        if f_name:
            stmt = select(Flavor).where(Flavor.product_id == product.id, Flavor.name == f_name)
            existing = await session.scalar(stmt)
            if not existing:
                session.add(Flavor(name=f_name, product_id=product.id))

    res = await session.execute(select(Flavor).where(Flavor.product_id == product.id))
    current_flavors = [f.name for f in res.scalars().all()]
    caption = get_product_caption(product, current_flavors)


    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.chat.id,
            message_id=data['product_msg_id'],
            caption=caption,
            reply_markup=get_product_edit_kb(product),
            parse_mode="HTML"
        )
    except: pass 

    try:
        await msg.delete()
        await msg.bot.delete_message(msg.chat.id, data['prompt_msg_id'])
    except: pass
    await state.clear()

@admin_router.callback_query(F.data.startswith("adm_act:del_flavor:"))
async def admin_remove_flavor_start(cb: CallbackQuery, state: FSMContext):
    p_id = int(cb.data.split(":")[2])
    await state.update_data(product_msg_id=cb.message.message_id, product_id=p_id)
    
    await state.set_state(AdminStates.waiting_del_flavors)
    prompt_msg = await cb.message.answer(_("edt_new_flavors_del"))
    await state.update_data(prompt_msg_id=prompt_msg.message_id)
    await cb.answer()

    

@admin_router.message(AdminStates.waiting_del_flavors, F.text)
async def admin_remove_flavor_save(msg: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    product = await session.get(Product, data['product_id'])
    
    flavors_to_remove = msg.text.splitlines()
    for name in flavors_to_remove:
        name = name.strip().capitalize() 
        if not name: continue
        
        stmt = select(Flavor).where(Flavor.product_id == product.id, Flavor.name == name)
        flavor = await session.scalar(stmt)
        if flavor:
            await session.delete(flavor)
            
    res = await session.execute(select(Flavor).where(Flavor.product_id == product.id))
    current_flavors = [f.name for f in res.scalars().all()]
    caption = get_product_caption(product, current_flavors)
    try:
        await msg.bot.edit_message_caption(
            chat_id=msg.chat.id,
            message_id=data['product_msg_id'],
            caption=caption,
            reply_markup=get_product_edit_kb(product),
            parse_mode="HTML"
        )
    except: pass

    try:
        await msg.delete()
        await msg.bot.delete_message(msg.chat.id, data['prompt_msg_id'])
    except: pass
    await state.clear()




@admin_router.callback_query(F.data == "admin_add_for_seller")
async def admin_add_product_choose_seller(
    cb: CallbackQuery,
    session: AsyncSession,
    user: User
):
    result = await session.execute(
        select(Seller)
        .options(selectinload(Seller.user))
        .order_by(User.full_name)
        .join(User)
    )
    sellers = result.scalars().all()

    if not sellers:
        return await cb.answer(_("sellers_now_found"), show_alert=True)

    buttons = []

    for s in sellers:
        seller_user = s.user

        name = (
            f"@{seller_user.username}"
            if seller_user.username
            else seller_user.full_name
        )

        buttons.append([
            InlineKeyboardButton(
                text=f"👤 {name}",
                callback_data=f"as_sel_{s.id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text=_("back"),
            callback_data="admin_back"
        )
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await cb.message.edit_text(
        _("choose_seller_2"),
        reply_markup=kb
    )



@admin_router.callback_query(F.data.startswith("as_sel_"))
async def admin_add_choose_seller(cb: CallbackQuery, state: FSMContext, session: AsyncSession):
    seller_id = int(cb.data.replace("as_sel_", ""))

    seller = await session.get(Seller, seller_id)
    if not seller:
        return await cb.answer("Продавец не найден", show_alert=True)

    if not seller.is_active:
        return await cb.answer(
            "❌ Продавец деактивирован",
            show_alert=True
        )
    
    msg = await cb.message.edit_text(
        _("choose_city"),
        reply_markup=await admin_cities_select_kb(session),
        parse_mode="HTML"
    )

    await state.set_state(AdminAddProduct.city)
    await state.update_data(
        seller_id=seller.id,
        seller_user_id=seller.user_id,
        bot_msg_id=msg.message_id
    )




@admin_router.callback_query(AdminAddProduct.city, F.data.startswith("city_"))
async def admin_add_city(cb: CallbackQuery, state: FSMContext):
    city_id = int(cb.data.replace("city_", ""))
    
    await state.update_data(city_id=city_id)
    await state.set_state(AdminAddProduct.name)

    await cb.message.edit_text(
        _("adm_add_name"),
        reply_markup=admin_cancel_kb()
    )






@admin_router.message(AdminAddProduct.name)
async def admin_add_name(msg: Message, state: FSMContext, session: AsyncSession):
    if not msg.text or len(msg.text) > 25:
        return await msg.answer(_("simvols_error"))

    await state.update_data(name=msg.text)
    data = await state.get_data()
    await msg.delete() 

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("adm_add_brand"),
        reply_markup=await admin_brands_kb(session)
    )
    await state.set_state(AdminAddProduct.brand)


@admin_router.callback_query(AdminAddProduct.brand, F.data.startswith("adm_brand:"))
async def admin_add_brand(cb: CallbackQuery, state: FSMContext):
    brand = cb.data.split(":", 1)[1]
    await state.update_data(brand=brand)

    await cb.message.edit_text(
        _("adm_add_tyags"),
        reply_markup=admin_cancel_kb()
    )
    await state.set_state(AdminAddProduct.puffs)
    await cb.answer()

@admin_router.message(AdminAddProduct.brand, F.text)
async def admin_add_brand_message(msg: Message, state: FSMContext):
    brand = msg.text.strip()

    await state.update_data(brand=brand)

    data = await state.get_data()

    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("adm_add_tyags"),
        reply_markup=admin_cancel_kb()
    )

    await state.set_state(AdminAddProduct.puffs)


@admin_router.message(AdminAddProduct.puffs)
async def admin_add_puffs(msg: Message, state: FSMContext):
    if not msg.text.isdigit(): return await msg.answer(_("error_string"))
    
    await state.update_data(puffs=int(msg.text))
    data = await state.get_data()
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("adm_add_strength"),
        reply_markup=strengths_kb()
    )
    await state.set_state(AdminAddProduct.strength)



@admin_router.message(AdminAddProduct.strength)
async def admin_add_strength(msg: Message, state: FSMContext):
    if not msg.text.isdigit(): return await msg.answer(_("error_string"))

    await state.update_data(strength=int(msg.text))
    data = await state.get_data()
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],


        text=_("adm_add_price"),
        reply_markup=admin_cancel_kb()
    )
    await state.set_state(AdminAddProduct.price)

@admin_router.message(AdminAddProduct.price)
async def admin_add_price(msg: Message, state: FSMContext):
    try:
        price = Decimal(msg.text.replace(",", "."))
    except: return await msg.answer(_("price_error"))

    await state.update_data(price=price)
    data = await state.get_data()
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("adm_add_photo"),
        reply_markup=admin_cancel_kb()
    )
    await state.set_state(AdminAddProduct.photo)

@admin_router.message(AdminAddProduct.photo, F.photo)
async def admin_add_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    
    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("second_for_photo")
    )

    file_id = msg.photo[-1].file_id
    file = await msg.bot.get_file(file_id)
    file_bytes = await msg.bot.download_file(file.file_path)
    
    await state.update_data(photo_bytes=file_bytes.read())
    await msg.delete()

    await msg.bot.edit_message_text(
        chat_id=msg.chat.id,
        message_id=data["bot_msg_id"],
        text=_("adm_add_flavors"),
        reply_markup=admin_cancel_kb()
    )
    await state.set_state(AdminAddProduct.flavors)




@admin_router.message(AdminAddProduct.flavors)
async def admin_confirm_add(
    msg: Message,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()

    city = await session.get(City, data["city_id"])
    if not city:
        await state.clear()
        return await msg.answer("❌ Город не найден")

    seller = await session.get(Seller, data["seller_id"])
    if not seller:
        await state.clear()
        return await msg.answer("❌ Продавец не найден")

    seller_user = await session.get(User, seller.user_id)
    seller_display_name = (
        f"@{seller_user.username}"
        if seller_user and seller_user.username
        else seller_user.full_name
    )

    image = Image.open(BytesIO(data["photo_bytes"])).convert("RGB")
    square = crop_to_square(image)

    buffer = BytesIO()
    square.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)

    temp_msg = await msg.bot.send_photo(
        chat_id=msg.chat.id,
        photo=BufferedInputFile(buffer.getvalue(), "preview.jpg")
    )

    tg_file_id = temp_msg.photo[-1].file_id
    await temp_msg.delete()

    product = Product(
        name=data["name"],
        city_id=city.id,
        seller_id=seller.id,
        brand=data["brand"],
        quantity_tyg=data["puffs"],
        strength_mg=data["strength"],
        price=data["price"],
        image_path=tg_file_id,
        in_stock=True
    )

    session.add(product)
    await session.flush()

    for line in msg.text.splitlines():
        name = line.strip().capitalize()
        if name:
            session.add(
                Flavor(name=name, product_id=product.id)
            )

    await state.clear()

    await msg.answer(
        _("product_succesfully_add_for_sel",
          product_name=product.name,
          seller_display_name=seller_display_name),
        parse_mode="HTML"
    )

    await msg.answer(
        _("back_to_adm_panel"),
        reply_markup=admin_panel_kb(),
        parse_mode="HTML"
    )




@admin_router.callback_query(F.data == "admin_feedbacks")
async def admin_feedbacks(cb: CallbackQuery, session: AsyncSession):
    stmt = (
        select(Feedback)
        .order_by(Feedback.created_at.desc())
        .limit(20)
        .options(selectinload(Feedback.user))
    )
    feedbacks = (await session.execute(stmt)).scalars().all()

    if not feedbacks:
        return await cb.answer(_("admin_feedbacks_empty"), show_alert=True)

    await cb.message.edit_text(
        _("admin_feedbacks_title"),
        reply_markup=admin_feedbacks_list_kb(feedbacks)
    )



@admin_router.callback_query(F.data.startswith("admin_fb:"))
async def admin_feedback_view(
    cb: CallbackQuery,
    session: AsyncSession,
    state: FSMContext
):
    fb_id = int(cb.data.split(":")[1])

    stmt = (
        select(Feedback)
        .where(Feedback.id == fb_id)
        .options(selectinload(Feedback.user))
    )

    fb = (await session.execute(stmt)).scalar_one_or_none()
    if not fb:
        return await cb.answer(_("admin_feedback_not_found"))

    await state.update_data(
        feedback_id=fb_id,
        feedback_message_id=cb.message.message_id
    )

    riga_tz = ZoneInfo("Europe/Riga")
    created_time = fb.created_at.astimezone(riga_tz).strftime("%d.%m.%Y %H:%M") 
    
    user_display = format_buyer(fb.user)

    text = (
        _("admin_feedback_view",
        user=user_display,
        message=fb.message
        )
        + f"\n\n⏰ {created_time}"
    )

    await cb.message.edit_text(
        text,
        reply_markup=admin_feedback_actions_kb(
            fb.id,
            fb.is_processed
        )
    )




async def notify_admins_new_feedback(
    session: AsyncSession,
    feedback_id: int
):
    feedback = await session.get(Feedback, feedback_id)
    if not feedback:
        return

    stmt = select(User).where(
        User.role.in_(["admin", "super_admin"])
    )
    admins = (await session.execute(stmt)).scalars().all()

    for admin in admins:
        if not admin.notifications_enabled:
            continue

        with use_lang(admin.language):  
            text = _(
                "admin_feedback_notify",
                message=feedback.message[:1000],
                id=feedback.id
            )

        try:
            await bot.send_message(admin.tg_id, text, parse_mode="HTML")
        except Exception as e:
            print(f"Admin notify error {admin.tg_id}: {e}")



@admin_router.callback_query(F.data.startswith("admin_fb_del:"))
async def admin_feedback_delete(cb: CallbackQuery, session: AsyncSession):
    fb_id = int(cb.data.split(":")[1])

    feedback = await session.get(Feedback, fb_id)
    if not feedback:
        return await cb.answer(_("admin_feedback_already_deleted"))

    await session.delete(feedback)
    await session.commit()

    await cb.answer(_("admin_feedback_deleted"))

    await cb.message.edit_text(
        _("admin_feedback_deleted_text"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=_("back_feedbacks"),
                        callback_data="admin_back"
                    )
                ]
            ]
        )
    )

@admin_router.callback_query(F.data.startswith("admin_fb_reply:"))
async def admin_feedback_reply_start(
    cb: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    fb_id = int(cb.data.split(":")[1])

    feedback = await session.get(Feedback, fb_id)
    if not feedback:
        return await cb.answer(_("admin_feedback_not_found"), show_alert=True)

    await state.update_data(
        feedback_id=fb_id,
        feedback_message_id=cb.message.message_id
    )

    msg = await cb.message.answer(
        _("admin_feedback_enter_reply"),
        reply_markup=admin_cancel_kb()
    )

    await state.update_data(prompt_message_id=msg.message_id)
    await state.set_state(AdminFeedback.answer)

    await cb.answer()




@admin_router.message(AdminFeedback.answer)
async def admin_feedback_send_reply(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    data = await state.get_data()
    fb_id = data.get("feedback_id")
    feedback_message_id = data.get("feedback_message_id")
    prompt_message_id = data.get("prompt_message_id")

    feedback = await session.get(Feedback, fb_id)
    if not feedback:
        await state.clear()
        return await message.answer(_("admin_feedback_not_found"))

    user = await session.get(User, feedback.user_id)
    if not user:
        await state.clear()
        return await message.answer(_("user_not_found"))

    reply_text = message.text.strip()

    with use_lang(user.language):
        text = _(
            "feedback_reply_from_admin",
            reply=reply_text
        )

    try:
        await message.bot.send_message(
            user.tg_id,
            text,
            parse_mode="HTML"
        )
    except Exception:
        await message.answer(_("feedback_reply_failed"))
        await state.clear()
        return


    feedback.is_processed = True
    feedback.processed_at = func.now()
    await session.commit()


    try:
        await message.delete()
    except:
        pass

    if prompt_message_id:
        try:
            await message.bot.delete_message(
                message.chat.id,
                prompt_message_id
            )
        except:
            pass

    if feedback_message_id:
        try:
            await message.bot.delete_message(
                message.chat.id,
                feedback_message_id
            )
        except:
            pass

    await state.clear()


    stmt = (
        select(Feedback)
        .order_by(Feedback.created_at.desc())
        .limit(20)
    )
    feedbacks = (await session.execute(stmt)).scalars().all()

    if feedbacks:
        await message.answer(
            _("admin_feedbacks_title"),
            reply_markup=admin_feedbacks_list_kb(feedbacks)
        )
    else:
        await message.answer(
            _("admin_feedbacks_empty"),
            reply_markup=admin_panel_kb()
        )





def format_buyer(user) -> str:
    full_name = user.full_name.strip() if user.full_name else "Без имени"

    if user.username:
        return f"{full_name} | @{user.username}"
    
    return f"{full_name} | ID: {user.tg_id}"




def format_seller(user) -> str:
    if user.username:
        return f"@{user.username}"

    if user.full_name and user.full_name.strip():
        return f"ID:{user.tg_id} | {user.full_name}"

    return f"ID:{user.tg_id}"

@admin_router.callback_query(F.data == "admin_orders")
async def admin_orders(cb: CallbackQuery, session: AsyncSession):
    stmt = (
        select(Order)
        .where(Order.status == "pending") 
        .order_by(Order.created_at.desc())
        .options(
            selectinload(Order.user),
            selectinload(Order.seller).selectinload(Seller.user),
            selectinload(Order.product)
        )
    )

    orders = (await session.execute(stmt)).scalars().all()

    if not orders:
        await cb.message.edit_text(
            _("admin_orders_empty"),
            reply_markup=admin_panel_kb()
        )
        return

    kb = InlineKeyboardBuilder()

    for order in orders:
        seller_display = format_seller(order.seller.user)

        kb.button(
            text=f"📦 #{order.id} | {seller_display}",
            callback_data=f"admin_order_view:{order.id}"
        )

    kb.button(text=_("back_btn"), callback_data="admin_back")
    kb.adjust(1)

    await cb.message.edit_text(
        _("admin_orders_title"),
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )




@admin_router.callback_query(F.data.startswith("admin_order_view:"))
async def admin_order_view(cb: CallbackQuery, session: AsyncSession):
    order_id = int(cb.data.split(":")[-1])

    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(
            selectinload(Order.user),
            selectinload(Order.product),
            selectinload(Order.seller).selectinload(Seller.user),
            selectinload(Order.flavors).selectinload(OrderFlavor.flavor)
        )
    )

    order = (await session.execute(stmt)).scalar_one_or_none()

    if not order:
        return await cb.answer(_("order_not_found"), show_alert=True)

    if order.status != "pending":
        await cb.answer(_("order_already_processed"), show_alert=True)
        return await admin_orders(cb, session)

    seller_display = format_seller(order.seller.user)
    buyer_display = format_buyer(order.user)

    flavor_items = [
        _("order_flavor_item", name=of.flavor.name, qty=of.quantity)
        for of in order.flavors
    ]
    flavors = ", ".join(flavor_items) or _("no_flavors")

    status = _(f"status_{order.status}")

    text = (
        f"{_('order_view_title', id=order.id)}\n"
        f"{_('order_buyer', buyer=buyer_display)}\n"
        f"{_('order_seller', seller=seller_display)}\n"
        f"{_('order_product', name=order.product.name)}\n"
        f"{_('order_puffs', puffs=order.quantity_tyg)}\n"
        f"{_('order_view_flavors', flavors=flavors)}\n"
        f"{_('order_price', price=order.total_price)}\n\n"
        f"📌 {_('status_label')}: <b>{status}</b>"
    )

    await cb.message.edit_text(
        text,
        reply_markup=admin_order_card_kb(order.id, order.status),
        parse_mode="HTML"
    )






@admin_router.callback_query(F.data.startswith("admin_order:cancel:"))
async def admin_cancel_order(cb: CallbackQuery, session: AsyncSession):
    order_id = int(cb.data.split(":")[-1])
    order = await session.get(Order, order_id)

    if order.status != "pending":
        return await cb.answer(_("order_already_processed"), show_alert=True)
    
    if order:
        order.status = "cancelled"
        await session.commit()
        await cb.answer(_("order_cancelled_well", id=order.id))

    await admin_orders(cb, session)



@admin_router.callback_query(F.data.startswith("admin_order:confirm:"))
async def admin_confirm_order(cb: CallbackQuery, session: AsyncSession):
    order_id = int(cb.data.split(":")[-1])
    order = await session.get(Order, order_id)

    if order.status != "pending":
        return await cb.answer(_("order_already_processed"), show_alert=True)

    if not order:
        return await cb.answer(_("not_order"), show_alert=True)

    order.status = "confirmed"
    await session.commit()

    await cb.answer(_("order_complete_well", order_number=order.id))
    await admin_orders(cb, session)




@admin_router.callback_query(F.data.startswith("admin_order:complete:"))
async def admin_complete_order(cb: CallbackQuery, session: AsyncSession):
    order_id = int(cb.data.split(":")[-1])
    order = await session.get(Order, order_id)

    if not order:
        return await cb.answer(_("not_order"), show_alert=True)

    order.status = "completed"
    order.completed_at = func.now()
    await session.commit()

    await admin_order_view(cb, session)