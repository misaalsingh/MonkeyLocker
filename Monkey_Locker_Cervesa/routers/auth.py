from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, GoogleTokenRequest
from services.db_connection import get_db
from services.auth_service import AuthService
from services.facial_recognition import FaceRecognitionService
from services.event_logger import EventLogger
from models.users import User

router = APIRouter()

# Initialize services
auth_service = AuthService()
face_service = FaceRecognitionService()
event_logger = EventLogger()


def get_client_info(request: Request) -> dict:
    """Extract client IP and user agent from request"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    }

@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    
    client_info = get_client_info(request)
    
    try:
        # Register user using auth service
        user = auth_service.register_user(
            db=db,
            username=payload.username,
            email=payload.email,
            password=payload.password
        )
        
        # Create JWT token
        token = auth_service.create_token(user.id)
        
        # Log successful registration
        event_logger.log(
            db=db,
            event_type="user_registration",
            success=True,
            user_id=user.id,
            **client_info
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_oauth_user": False
            }
        }
    
    except HTTPException as e:
        # Log failed registration attempt
        event_logger.log(
            db=db,
            event_type="user_registration",
            success=False,
            event_metadata={"email": payload.email, "error": e.detail},
            **client_info
        )
        raise


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    
    client_info = get_client_info(request)
    
    # Authenticate user
    user = auth_service.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password
    )
    
    if not user:
        # Log failed login attempt
        event_logger.log(
            db=db,
            event_type="login_attempt",
            success=False,
            event_metadata={"email": payload.email, "method": "password"},
            **client_info
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create JWT token
    token = auth_service.create_token(user.id)
    
    # Log successful login
    event_logger.log(
        db=db,
        event_type="login_attempt",
        success=True,
        user_id=user.id,
        metadata={"method": "password"},
        **client_info
    )
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_oauth_user": user.is_oauth_user,
            "profile_picture": user.profile_picture_url
        }
    }

@router.post("/enroll-face")
async def enroll_face(
    user_id: int,
    face_image: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    
    client_info = get_client_info(request) if request else {}
    image_bytes = await face_image.read()
    
    try:
        # Enroll face using face service
        result = face_service.enroll_face(db, user_id, image_bytes)
        
        # Log successful enrollment
        event_logger.log(
            db=db,
            event_type="face_enrollment",
            success=True,
            user_id=user_id,
            **client_info
        )
        
        return result
    
    except ValueError as e:
        # Log failed enrollment
        event_logger.log(
            db=db,
            event_type="face_enrollment",
            success=False,
            user_id=user_id,
            event_metadata={"error": str(e)},
            **client_info
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login-face", response_model=TokenResponse)
async def login_face(
    face_image: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    
    client_info = get_client_info(request) if request else {}
    image_bytes = await face_image.read()
    
    try:
        # Authenticate using face service
        user_id, confidence = face_service.authenticate_face(db, image_bytes)
        
        if user_id is None:
            # Log failed face login
            event_logger.log(
                db=db,
                event_type="face_login_attempt",
                success=False,
                event_metadata={"method": "face"},
                **client_info
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Face not recognized"
            )
        
        # Get user details
        user = db.query(User).filter(User.id == user_id).first()
        
        # Log successful face login
        event_logger.log(
            db=db,
            event_type="face_login_attempt",
            success=True,
            user_id=user_id,
            confidence_score=confidence,
            event_metadata={"method": "face"},
            **client_info
        )
        
        # Create JWT token
        token = auth_service.create_token(user_id)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_oauth_user": user.is_oauth_user,
                "profile_picture": user.profile_picture_url
            },
            "confidence": confidence
        }
    
    except ValueError as e:
        # Log error (no face detected)
        event_logger.log(
            db=db,
            event_type="face_login_attempt",
            success=False,
            event_metadata={"error": str(e)},
            **client_info
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========== Google OAuth2 ==========

@router.get("/google/login")
async def google_login():
    auth_url = auth_service.get_google_login_url()
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    client_info = get_client_info(request)
    
    try:
        # Handle Google OAuth callback
        user, token = await auth_service.handle_google_callback(db, code)
        
        # Log successful OAuth login
        event_logger.log(
            db=db,
            event_type="oauth_login",
            success=True,
            user_id=user.id,
            event_metadata={"provider": "google"},
            **client_info
        )
        
        # Redirect to frontend with token
        frontend_url = f"http://localhost:3000/auth/callback?token={token}"
        return RedirectResponse(url=frontend_url)
    
    except Exception as e:
        # Log failed OAuth attempt
        event_logger.log(
            db=db,
            event_type="oauth_login",
            success=False,
            event_metadata={"provider": "google", "error": str(e)},
            **client_info
        )
    
        frontend_url = f"http://localhost:3000/auth/error?message={str(e)}"
        return RedirectResponse(url=frontend_url)


@router.post("/google/verify", response_model=TokenResponse)
async def google_verify_token(
    payload: GoogleTokenRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    
    client_info = get_client_info(request)
    
    try:
        # Verify Google ID token
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.id_token}"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            google_user_info = response.json()
        
        # Get or create user
        user = auth_service._get_or_create_oauth_user(db, google_user_info, "google")
        
        # Log successful OAuth login
        event_logger.log(
            db=db,
            event_type="oauth_login",
            success=True,
            user_id=user.id,
            event_metadata={"provider": "google", "method": "id_token"},
            **client_info
        )
        
        # Create JWT token
        token = auth_service.create_token(user.id)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_oauth_user": True,
                "profile_picture": user.profile_picture_url
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Log failed OAuth attempt
        event_logger.log(
            db=db,
            event_type="oauth_login",
            success=False,
            event_metadata={"provider": "google", "error": str(e)},
            **client_info
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth verification failed: {str(e)}"
        )

@router.get("/me")
async def get_current_user_info(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    user = auth_service.get_current_user(db, token)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_oauth_user": user.is_oauth_user,
        "oauth_provider": user.oauth_provider,
        "profile_picture": user.profile_picture_url,
        "face_enrolled": user.face_embedding is not None,
        "created_at": user.created_at
    }


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        user = auth_service.get_current_user(db, token)
        
        client_info = get_client_info(request) if request else {}
        
        # Log logout event
        event_logger.log(
            db=db,
            event_type="user_logout",
            success=True,
            user_id=user.id,
            **client_info
        )
    
    return {"message": "Logged out successfully"}


@router.post("/refresh")
async def refresh_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    token = authorization.split(" ")[1]
    user = auth_service.get_current_user(db, token)
    
    # Create new token
    new_token = auth_service.create_token(user.id)
    
    return {
        "access_token": new_token,
        "token_type": "bearer"
    }