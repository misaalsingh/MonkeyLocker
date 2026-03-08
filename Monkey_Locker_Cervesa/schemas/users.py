# schemas/users.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserRead(BaseModel):
    id: int
    firstname: str
    lastname: str
    username: str
    email: str
    age: Optional[int]
    is_active: bool
    is_verified: bool
    is_oauth_user: bool
    face_enrolled: bool = False 
    created_at: datetime
    last_updated: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    age: Optional[int] = None
    secret_name: Optional[str] = None

class UserCreate(BaseModel):
    id: int
    firstname: str
    lastname: str
    username: str
    email: str
    age: Optional[int]
    is_active: bool
    is_verified: bool
    is_oauth_user: bool
    face_enrolled: bool = False 
    created_at: datetime
    last_updated: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserStatusResponse(BaseModel):
    user_id: int
    username: str
    is_active: bool
    is_verified: bool
    is_deleted: bool
    is_oauth_user: bool
    face_enrolled: bool
    timestamps: dict
    deactivation_reason: Optional[str]