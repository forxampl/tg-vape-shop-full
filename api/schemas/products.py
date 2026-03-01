from pydantic import BaseModel
from typing import List, Optional


class FlavorOut(BaseModel):
    id: int
    name: str
    
class ProductSchema(BaseModel):
    id: int
    name: str
    price: float
    image_file_id: str  
    city: str

class ProductListOut(BaseModel):
    id: int
    name: str
    price: float
    puffs: int
    strength: int
    brand: Optional[str]
    in_stock: bool
    image: Optional[str]


class ProductDetailOut(ProductListOut):
    flavors: List[FlavorOut]
    seller_id: int
    city_id: int