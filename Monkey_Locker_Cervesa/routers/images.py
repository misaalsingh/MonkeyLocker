from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, time
from services.db_connection import get_db
from models.images import Image
from models.rooms import RoomMember
from schemas.images import ImageRead, ImageUpdate
from dependencies.auth import get_current_user
from dependencies.context import get_client_info
from services.event_logger import EventLogger
from services.storage import StorageService
from models.users import User

router = APIRouter()
event_logger = EventLogger()
storage = StorageService()


def _serialize(img: Image) -> dict:
    """Return image as dict, replacing image_url with a presigned URL when using S3."""
    return {
        "id": img.id,
        "room_id": img.room_id,
        "uploaded_by": img.uploaded_by,
        "image_url": storage.get_file_url(img.filename),
        "caption": img.caption,
        "uploaded_at": img.uploaded_at,
    }


def _require_membership(room_id: int, user_id: int, db: Session) -> RoomMember:
    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="You are not a member of this room")
    return member


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/rooms/{room_id}/images", response_model=ImageRead, status_code=201)
async def upload_image(
    room_id: int,
    image: UploadFile = File(...),
    caption: str = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    _require_membership(room_id, current_user.id, db)

    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    filename, url = await storage.upload_file(image, prefix=f"locker/images/rooms/{room_id}")

    img = Image(
        room_id=room_id,
        uploaded_by=current_user.id,
        filename=filename,
        image_url=url,
        caption=caption
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    event_logger.log(
        db=db,
        event_type="image_uploaded",
        event_category=EventLogger.CATEGORY_IMAGE,
        success=True,
        user_id=current_user.id,
        event_metadata={"room_id": room_id, "image_id": img.id},
        **client_info
    )

    return _serialize(img)


@router.get("/rooms/{room_id}/images", response_model=List[ImageRead])
def list_images(
    room_id: int,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _require_membership(room_id, current_user.id, db)
    query = db.query(Image).filter(Image.room_id == room_id)
    if date_from:
        query = query.filter(Image.uploaded_at >= datetime.combine(date_from, time.min))
    if date_to:
        query = query.filter(Image.uploaded_at <= datetime.combine(date_to, time.max))
    images = query.order_by(Image.uploaded_at.desc()).all()
    return [_serialize(img) for img in images]


@router.patch("/images/{image_id}", response_model=ImageRead)
def update_image(
    image_id: int,
    payload: ImageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    img = db.query(Image).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    if img.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the uploader can edit this image")

    if payload.caption is not None:
        img.caption = payload.caption

    db.commit()
    db.refresh(img)
    return _serialize(img)


@router.delete("/images/{image_id}", status_code=204)
def delete_image(
    image_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    img = db.query(Image).filter(Image.id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Allow uploader or room admin to delete
    is_uploader = img.uploaded_by == current_user.id
    is_admin = db.query(RoomMember).filter(
        RoomMember.room_id == img.room_id,
        RoomMember.user_id == current_user.id,
        RoomMember.role.in_(["admin", "moderator"])
    ).first()

    if not is_uploader and not is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this image")

    storage.delete_file(img.filename)
    db.delete(img)
    db.commit()

    event_logger.log(
        db=db,
        event_type="image_deleted",
        event_category=EventLogger.CATEGORY_IMAGE,
        success=True,
        user_id=current_user.id,
        event_metadata={"image_id": image_id, "room_id": img.room_id},
        **client_info
    )
