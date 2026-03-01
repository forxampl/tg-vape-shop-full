from aiogram.fsm.state import StatesGroup, State

class AdminStatesOld(StatesGroup):
    change_role = State()

class AdminStates(StatesGroup):
    waiting_city_add = State()
    confirm_city_translation = State()
    manual_city_translation = State()
    waiting_city_del = State()
    wait_city_name = State()
    add_city = State()
    delete_city = State()
    waiting_role_data = State() 
    change_role = State()
    waiting_broadcast = State() 
    waiting_broadcast_text = State()
    waiting_del_flavors = State()
    waiting_add_flavors = State()
    waiting_edit_photo = State()
    waiting_edit_value = State()
    waiting_seller_for_add = State()
    
class AdminAddProduct(StatesGroup):
    seller = State()
    city = State()
    name = State()
    brand = State()
    puffs = State()
    strength = State()
    price = State()
    photo = State()
    flavors = State()
    confirm = State()


class AdminFeedback(StatesGroup):
    answer = State()