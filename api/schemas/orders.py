from pydantic import BaseModel
from typing import List
from datetime import datetime


class OrderFlavorIn(BaseModel):
    flavor_id: int
    quantity: int


class OrderCreateIn(BaseModel):
    product_id: int
    flavors: List[OrderFlavorIn]


class OrderOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    total_price: float
    created_at: datetime


class OrderCreateOut(BaseModel):
    order_id: int
    seller_tg: str
    text: str

