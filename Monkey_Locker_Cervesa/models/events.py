# models/event.py
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import DateTime, String, Text, Integer, Boolean, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from typing import Optional, Dict, Any
from datetime import datetime


class Event(SQLModel, table=True):
    __tablename__ = "events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    # Event Details
    event_type: str = Field(nullable=False, index=True)
    event_category: Optional[str] = Field(default=None, index=True)  # 'auth', 'user', 'room', 'image', 'security'
    success: bool = Field(nullable=False, index=True)
    # User Info
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    target_user_id: Optional[int] = Field(default=None, foreign_key="users.id")  # For actions on other users
    # Related Entities
    # room_id: Optional[int] = Field(default=None, foreign_key="rooms.id")
    # image_id: Optional[int] = Field(default=None, foreign_key="images.id")
    # Security Info
    confidence_score: Optional[float] = Field(default=None)
    ip_address: Optional[str] = Field(default=None, index=True)
    user_agent: Optional[str] = Field(default=None, sa_column=Column(Text))
    # Additional Data
    event_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON)
    )
    # Error Info
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    # Timestamp
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), index=True)
    )