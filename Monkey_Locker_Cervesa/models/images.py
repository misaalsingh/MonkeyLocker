from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, Text
from sqlalchemy.sql import func
from typing import Optional
from datetime import datetime


class Image(SQLModel, table=True):
    __tablename__ = "images"

    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="rooms.id", index=True)
    uploaded_by: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    filename: str = Field(nullable=False)          # stored filename (used for deletion)
    image_url: str = Field(nullable=False)          # public URL served to clients
    caption: Optional[str] = Field(default=None, sa_column=Column(Text))
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
