from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class ProductShort(BaseModel):
    id: int
    name: str
    price: Decimal
    puffs: int 
    image_url: Optional[str]
    in_stock: bool
    brand: str


class ProductDetail(ProductShort):
    strength: int 
    flavors: List[str] 
    seller_name: str


class OrderCreate(BaseModel):
    tg_id: int
    product_id: int
    flavor_name: str
    quantity: int