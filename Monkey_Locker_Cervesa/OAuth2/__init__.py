# OAuth2/__init__.py (CORRECT)
from .jwt import JWTManager
from .password import PasswordManager
from .oauth import GoogleOAuth

__all__ = [
    "JWTManager",
    "PasswordManager", 
    "GoogleOAuth"
]