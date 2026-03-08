# models/user.py
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import LargeBinary, DateTime, String, Boolean, Integer
from sqlalchemy.sql import func
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    # Basic Info
    id: Optional[int] = Field(default=None, primary_key=True)
    firstname: Optional[str] = Field(default=None)
    lastname: Optional[str] = Field(default=None)
    username: str = Field(index=True, nullable=False, unique=True)
    email: str = Field(index=True, nullable=False, unique=True)
    password_hash: Optional[str] = Field(default=None)
    # Face Recognition
    face_embedding: Optional[bytes] = Field(
        default=None,
        sa_column=Column(LargeBinary)
    )
    face_enrolled_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    # Additional Info
    age: Optional[int] = Field(default=None, index=True)
    secret_name: Optional[str] = Field(default=None)
    profile_picture_url: Optional[str] = Field(default=None)
    
    # OAuth Info
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    oauth_provider: Optional[str] = Field(default=None)  # 'google', 'github', etc.
    is_oauth_user: bool = Field(default=False)
    

    is_active: bool = Field(default=True, index=True)
    is_verified: bool = Field(default=False)  # Email verification
    is_deleted: bool = Field(default=False)  # Soft delete
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    deactivated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    deactivation_reason: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now()
        )
    )
    last_login_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )
    password_changed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True))
    )