from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_private: Optional[bool] = None
    is_archived: Optional[bool] = None


class RoomMemberRead(BaseModel):
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class RoomRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_by: Optional[int]
    is_private: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoomDetailRead(RoomRead):
    members: list[RoomMemberRead] = []
