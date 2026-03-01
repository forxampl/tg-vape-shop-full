from pydantic import BaseModel
from typing import Optional


class UserProfileOut(BaseModel):
    id: int
    username: Optional[str]
    full_name: Optional[str]
    role: str
    language: str
    notifications_enabled: bool


class UserLanguageIn(BaseModel):
    language: str

