from aiogram.fsm.state import StatesGroup, State

class SellerAddProduct(StatesGroup):
    city = State()
    name = State()
    brand = State()
    puffs = State()
    strength = State()
    price = State()
    photo = State()
    flavors = State()
    confirm = State()

class SellerEditProduct(StatesGroup):
    waiting_edit_value = State()
    waiting_edit_photo = State()

    city = State()
    product = State()
    edit_action = State()   
    add_flavors = State()       
    remove_flavors = State()    
    confirm_delete = State()   
    waiting_value = State()