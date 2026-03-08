from pydantic import BaseModel
from typing import Optional


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class UserInfo(BaseModel):
    """OAuth user info"""
    id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str  # 'google', 'github', etc.


class LoginCredentials(BaseModel):
    email: str
    password: str


class RegisterData(BaseModel):
    username: str
    email: str
    password: str