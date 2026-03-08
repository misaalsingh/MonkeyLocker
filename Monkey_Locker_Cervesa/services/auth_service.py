from sqlalchemy.orm import Session
from typing import Optional, Tuple
from fastapi import HTTPException, status
from OAuth2 import JWTManager, PasswordManager, GoogleOAuth
from models.users import User
import os
from dotenv import load_dotenv

load_dotenv()
class AuthService:
    
    def __init__(self):
        self.jwt = JWTManager(
            secret_key=os.getenv("SECRET_KEY"),
            expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        )
        
        self.password = PasswordManager()
        
        self.google_oauth = GoogleOAuth(
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
        )

    
    def register_user(self, db: Session, username: str, email: str, password: str) -> User:
        # Check if exists
        if db.query(User).filter((User.username == username) | (User.email == email)).first():
            raise HTTPException(400, "User already exists")
        hashed = self.password.hash(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=hashed,
            is_oauth_user=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user or user.is_oauth_user:
            return None
        
        if not self.password.verify(password, user.password_hash):
            return None
        
        return user
    
    def create_token(self, user_id: int) -> str:
        return self.jwt.create_token(user_id)
    
    def verify_token(self, token: str) -> Optional[int]:
        return self.jwt.extract_user_id(token)
    
    def get_current_user(self, db: Session, token: str) -> User:
        user_id = self.verify_token(token)
        
        if not user_id:
            raise HTTPException(401, "Invalid token")
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(401, "User not found")
        
        return user
    
    def get_google_login_url(self) -> str:
        
        return self.google_oauth.get_authorization_url()
    
    async def handle_google_callback(self, db: Session, code: str) -> Tuple[User, str]:
        user_info = await self.google_oauth.verify_and_get_user(code)
        
        user = self._get_or_create_oauth_user(db, user_info, "google")
        
        token = self.create_token(user.id)
        
        return user, token
    
    def _get_or_create_oauth_user(self, db: Session, oauth_info: dict, provider: str) -> User:
        google_id = oauth_info.get("id")
        email = oauth_info.get("email")
        
        user = db.query(User).filter(User.google_id == google_id).first()
        if user:
            return user
        
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            user.oauth_provider = provider
            user.is_oauth_user = True
            user.profile_picture_url = oauth_info.get("picture")
            db.commit()
            return user
        
        username = email.split("@")[0]
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            username=username,
            email=email,
            google_id=google_id,
            oauth_provider=provider,
            is_oauth_user=True,
            profile_picture_url=oauth_info.get("picture")
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    # def log_event(self, db: Session, event_type: str, success: bool, **kwargs):
    #     event = Event(
    #         event_type=event_type,
    #         success=success,
    #         **kwargs
    #     )
    #     db.add(event)
    #     db.commit()