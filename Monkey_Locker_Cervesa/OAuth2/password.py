from passlib.context import CryptContext
from typing import Optional


class PasswordManager:
    
    def __init__(self, schemes: list = None):
        if schemes is None:
            schemes = ["bcrypt"]
        
        self.pwd_context = CryptContext(schemes=schemes, deprecated="auto")
    
    def hash(self, password: str) -> str:
        return self.pwd_context.hash(password)
    
    def verify(self, plain_password: str, hashed_password: str) -> bool:

        return self.pwd_context.verify(plain_password, hashed_password)
    
    def needs_rehash(self, hashed_password: str) -> bool:
        return self.pwd_context.needs_update(hashed_password)