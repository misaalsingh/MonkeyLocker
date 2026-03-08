# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from services.db_connection import get_db
from models.users import User
from schemas.users import UserCreate, UserRead, UserUpdate
from dependencies.auth import get_current_user, require_face_enrolled
from dependencies.validation import get_user_or_404
from dependencies.pagination import PaginationParams
from dependencies.context import get_client_info
from services.auth_service import AuthService
from services.facial_recognition import FaceRecognitionService
from services.event_logger import EventLogger

router = APIRouter()

auth_service = AuthService()
face_service = FaceRecognitionService()
event_logger = EventLogger()



@router.post("/me/deactivate")
def deactivate_my_account(
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already deactivated"
        )
    
    # Deactivate account
    current_user.is_active = False
    current_user.deactivated_at = datetime.utcnow()
    current_user.deactivation_reason = reason
    
    db.commit()
    db.refresh(current_user)
    
    # Log deactivation
    event_logger.log(
        db=db,
        event_type="account_deactivated",
        event_category=EventLogger.CATEGORY_USER,
        success=True,
        user_id=current_user.id,
        event_metadata={
            "reason": reason,
            "deactivated_at": current_user.deactivated_at.isoformat()
        },
        **client_info
    )
    
    return {
        "message": "Account deactivated successfully",
        "deactivated_at": current_user.deactivated_at,
        "reason": reason
    }


@router.post("/me/reactivate")
def reactivate_my_account(
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Reactivate a deactivated account"""
    
    if current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already active"
        )
    
    # Reactivate account
    current_user.is_active = True
    current_user.deactivated_at = None
    current_user.deactivation_reason = None
    
    db.commit()
    db.refresh(current_user)
    
    # Log reactivation
    event_logger.log(
        db=db,
        event_type="account_reactivated",
        event_category=EventLogger.CATEGORY_USER,
        success=True,
        user_id=current_user.id,
        **client_info
    )
    
    return {
        "message": "Account reactivated successfully"
    }


@router.delete("/me/permanent")
def permanently_delete_account(
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    if current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already marked for deletion"
        )
    
    # Soft delete
    current_user.is_deleted = True
    current_user.is_active = False
    current_user.deleted_at = datetime.utcnow()
    
    db.commit()
    
    # Log deletion
    event_logger.log(
        db=db,
        event_type="account_deleted",
        event_category=EventLogger.CATEGORY_USER,
        success=True,
        user_id=current_user.id,
        event_metadata={
            "deleted_at": current_user.deleted_at.isoformat(),
            "recovery_deadline": (current_user.deleted_at.replace(day=current_user.deleted_at.day + 30)).isoformat()
        },
        **client_info
    )
    
    return {
        "message": "Account marked for permanent deletion",
        "deleted_at": current_user.deleted_at,
        "recovery_deadline_days": 30
    }

@router.patch("/me", response_model=UserRead)
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    
    update_data = payload.dict(exclude_unset=True)
    changed_fields = {}
    
    for key, value in update_data.items():
        if key == "password" and value:
            # Hash new password
            old_hash = current_user.password_hash
            current_user.password_hash = auth_service.password.hash(value)
            current_user.password_changed_at = datetime.utcnow()
            changed_fields["password"] = "changed"
            
            # Log password change separately
            event_logger.log(
                db=db,
                event_type="password_changed",
                event_category=EventLogger.CATEGORY_AUTH,
                success=True,
                user_id=current_user.id,
                event_metadata={"changed_at": current_user.password_changed_at.isoformat()},
                **client_info
            )
            
        elif key == "email" and value:
            # Check if email already exists
            existing = db.query(User).filter(
                User.email == value,
                User.id != current_user.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            old_email = current_user.email
            current_user.email = value
            changed_fields["email"] = {"old": old_email, "new": value}
            
        elif key == "username" and value:
            # Check if username already exists
            existing = db.query(User).filter(
                User.username == value,
                User.id != current_user.id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already in use"
                )
            old_username = current_user.username
            current_user.username = value
            changed_fields["username"] = {"old": old_username, "new": value}
            
        elif key not in ["id", "created_at", "last_updated", "password_hash", "face_embedding"]:
            old_value = getattr(current_user, key)
            setattr(current_user, key, value)
            changed_fields[key] = {"old": str(old_value), "new": str(value)}
    
    db.commit()
    db.refresh(current_user)
    
    # Log profile update with changed fields
    if changed_fields:
        event_logger.log_account_change(
            db=db,
            event_type="profile_updated",
            user_id=current_user.id,
            changed_fields=changed_fields,
            **client_info
        )
    
    return current_user

@router.post("/me/face", response_model=dict)
async def enroll_my_face(
    face_image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Enroll face for current user with timestamp tracking"""
    
    image_bytes = await face_image.read()
    
    try:
        result = face_service.enroll_face(db, current_user.id, image_bytes)
        
        # Update face_enrolled_at timestamp
        current_user.face_enrolled_at = datetime.utcnow()
        db.commit()
        
        # Log successful enrollment
        event_logger.log(
            db=db,
            event_type="face_enrollment",
            event_category=EventLogger.CATEGORY_AUTH,
            success=True,
            user_id=current_user.id,
            event_metadata={"enrolled_at": current_user.face_enrolled_at.isoformat()},
            **client_info
        )
        
        return {
            **result,
            "enrolled_at": current_user.face_enrolled_at
        }
    
    except ValueError as e:
        # Log failed enrollment
        event_logger.log(
            db=db,
            event_type="face_enrollment",
            event_category=EventLogger.CATEGORY_AUTH,
            success=False,
            user_id=current_user.id,
            error_message=str(e),
            event_metadata={"error": str(e)},
            **client_info
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/me/face/verify")
async def verify_my_face(
    face_image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.face_embedding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No face enrolled — enroll your face first"
        )
    image_bytes = await face_image.read()
    is_match, confidence = face_service.verify_face(db, current_user.id, image_bytes)
    return {"verified": is_match, "confidence": confidence}


@router.delete("/me/face")
def remove_my_face(
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    
    result = face_service.remove_face_enrollment(db, current_user.id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    
    # Clear face_enrolled_at timestamp
    current_user.face_enrolled_at = None
    db.commit()
    
    # Log face removal
    event_logger.log(
        db=db,
        event_type="face_unenrollment",
        event_category=EventLogger.CATEGORY_AUTH,
        success=True,
        user_id=current_user.id,
        **client_info
    )

    return result

@router.get("/me/status")
def get_account_status(
    current_user: User = Depends(get_current_user)
):
    """Get current account status and timestamps"""
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "is_deleted": current_user.is_deleted,
        "is_oauth_user": current_user.is_oauth_user,
        "face_enrolled": current_user.face_embedding is not None,
        "timestamps": {
            "created_at": current_user.created_at,
            "last_updated": current_user.last_updated,
            "last_login_at": current_user.last_login_at,
            "password_changed_at": current_user.password_changed_at,
            "face_enrolled_at": current_user.face_enrolled_at,
            "deactivated_at": current_user.deactivated_at,
            "deleted_at": current_user.deleted_at
        },
        "deactivation_reason": current_user.deactivation_reason if current_user.deactivated_at else None
    }