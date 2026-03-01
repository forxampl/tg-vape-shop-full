from pydantic import BaseModel

class BroadcastToggleIn(BaseModel):
    enabled: bool


class BroadcastStateOut(BaseModel):
    enabled: bool
