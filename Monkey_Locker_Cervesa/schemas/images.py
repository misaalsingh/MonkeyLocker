from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ImageRead(BaseModel):
    id: int
    room_id: int
    uploaded_by: Optional[int]
    image_url: str
    caption: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ImageUpdate(BaseModel):
    caption: Optional[str] = None
