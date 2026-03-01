from pydantic import BaseModel
from datetime import datetime


class FeedbackCreateIn(BaseModel):
    text: str


class FeedbackOut(BaseModel):
    id: int
    text: str
    created_at: datetime