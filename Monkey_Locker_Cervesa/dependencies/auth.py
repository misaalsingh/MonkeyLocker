from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from services.db_connection import get_db
from models.users import User
from services.auth_service import AuthService

auth_service = AuthService()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    
    try:
        user = auth_service.get_current_user(db, token)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def optional_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    
    try:
        user = auth_service.get_current_user(db, token)
        return user
    except:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    
    #Uncomment if you add is_active field to User model
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    return current_user


async def require_face_enrolled(
    current_user: User = Depends(get_current_user)
) -> User:
    
    if not current_user.face_embedding:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Face enrollment required for this action. Please enroll your face first."
        )
    
    return current_user


async def require_oauth_user(
    current_user: User = Depends(get_current_user)
) -> User:
    
    if not current_user.is_oauth_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action is only available for OAuth users"
        )
    
    return current_user


async def require_password_user(
    current_user: User = Depends(get_current_user)
) -> User:
    
    if current_user.is_oauth_user and not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OAuth users cannot change password. Please use your OAuth provider."
        )
    
    return current_user