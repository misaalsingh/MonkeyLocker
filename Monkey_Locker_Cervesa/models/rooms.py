from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, Text, String
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime


class Room(SQLModel, table=True):
    __tablename__ = "rooms"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_by: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    is_private: bool = Field(default=False)
    is_archived: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )


class RoomMember(SQLModel, table=True):
    __tablename__ = "room_members"

    room_id: int = Field(foreign_key="rooms.id", primary_key=True)
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role: str = Field(default="member", sa_column=Column(String(20)))  # admin, moderator, member
    joined_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
