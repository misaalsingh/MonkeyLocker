from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from services.db_connection import get_db
from models.rooms import Room, RoomMember
from schemas.rooms import RoomCreate, RoomUpdate, RoomRead, RoomDetailRead, RoomMemberRead
from dependencies.auth import get_current_user
from dependencies.context import get_client_info
from services.event_logger import EventLogger
from models.users import User

router = APIRouter()
event_logger = EventLogger()


def _get_room_or_404(room_id: int, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


def _get_membership(room_id: int, user_id: int, db: Session) -> RoomMember | None:
    return db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id
    ).first()


def _require_membership(room_id: int, user_id: int, db: Session) -> RoomMember:
    member = _get_membership(room_id, user_id, db)
    if not member:
        raise HTTPException(status_code=403, detail="You are not a member of this room")
    return member


def _require_admin(room_id: int, user_id: int, db: Session) -> RoomMember:
    member = _require_membership(room_id, user_id, db)
    if member.role not in ("admin", "moderator"):
        raise HTTPException(status_code=403, detail="Admin or moderator role required")
    return member


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=RoomRead, status_code=201)
def create_room(
    payload: RoomCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    room = Room(
        name=payload.name,
        description=payload.description,
        created_by=current_user.id,
        is_private=payload.is_private
    )
    db.add(room)
    db.flush()  # get room.id before commit

    # Creator is automatically an admin member
    db.add(RoomMember(room_id=room.id, user_id=current_user.id, role="admin"))
    db.commit()
    db.refresh(room)

    event_logger.log(
        db=db,
        event_type="room_created",
        event_category=EventLogger.CATEGORY_ROOM,
        success=True,
        user_id=current_user.id,
        event_metadata={"room_id": room.id, "room_name": room.name},
        **client_info
    )

    return room


@router.get("/", response_model=List[RoomRead])
def list_my_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = db.query(RoomMember).filter(RoomMember.user_id == current_user.id).all()
    room_ids = [m.room_id for m in memberships]
    return db.query(Room).filter(Room.id.in_(room_ids), Room.is_archived == False).all()


@router.get("/{room_id}", response_model=RoomDetailRead)
def get_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room = _get_room_or_404(room_id, db)

    if room.is_private:
        _require_membership(room_id, current_user.id, db)

    members = db.query(RoomMember).filter(RoomMember.room_id == room_id).all()
    return RoomDetailRead(
        **room.dict(),
        members=[RoomMemberRead.from_orm(m) for m in members]
    )


@router.patch("/{room_id}", response_model=RoomRead)
def update_room(
    room_id: int,
    payload: RoomUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    room = _get_room_or_404(room_id, db)
    _require_admin(room_id, current_user.id, db)

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)

    db.commit()
    db.refresh(room)

    event_logger.log(
        db=db,
        event_type="room_updated",
        event_category=EventLogger.CATEGORY_ROOM,
        success=True,
        user_id=current_user.id,
        event_metadata={"room_id": room_id, "changed": list(update_data.keys())},
        **client_info
    )

    return room


@router.delete("/{room_id}", status_code=204)
def delete_room(
    room_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    room = _get_room_or_404(room_id, db)

    if room.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the room creator can delete it")

    db.query(RoomMember).filter(RoomMember.room_id == room_id).delete()
    db.delete(room)
    db.commit()

    event_logger.log(
        db=db,
        event_type="room_deleted",
        event_category=EventLogger.CATEGORY_ROOM,
        success=True,
        user_id=current_user.id,
        event_metadata={"room_id": room_id},
        **client_info
    )


@router.post("/{room_id}/join", response_model=RoomMemberRead)
def join_room(
    room_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    room = _get_room_or_404(room_id, db)

    if room.is_private:
        raise HTTPException(status_code=403, detail="This room is private — you need an invitation")

    if _get_membership(room_id, current_user.id, db):
        raise HTTPException(status_code=400, detail="Already a member of this room")

    member = RoomMember(room_id=room_id, user_id=current_user.id, role="member")
    db.add(member)
    db.commit()
    db.refresh(member)

    event_logger.log(
        db=db,
        event_type="room_joined",
        event_category=EventLogger.CATEGORY_ROOM,
        success=True,
        user_id=current_user.id,
        event_metadata={"room_id": room_id},
        **client_info
    )

    return member


@router.delete("/{room_id}/leave", status_code=204)
def leave_room(
    room_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    _get_room_or_404(room_id, db)
    member = _require_membership(room_id, current_user.id, db)

    db.delete(member)
    db.commit()

    event_logger.log(
        db=db,
        event_type="room_left",
        event_category=EventLogger.CATEGORY_ROOM,
        success=True,
        user_id=current_user.id,
        event_metadata={"room_id": room_id},
        **client_info
    )


@router.get("/{room_id}/members", response_model=List[RoomMemberRead])
def list_members(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _get_room_or_404(room_id, db)
    _require_membership(room_id, current_user.id, db)
    return db.query(RoomMember).filter(RoomMember.room_id == room_id).all()


@router.delete("/{room_id}/members/{user_id}", status_code=204)
def remove_member(
    room_id: int,
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    _get_room_or_404(room_id, db)
    _require_admin(room_id, current_user.id, db)

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Use the leave endpoint to remove yourself")

    target = _get_membership(room_id, user_id, db)
    if not target:
        raise HTTPException(status_code=404, detail="User is not a member of this room")

    db.delete(target)
    db.commit()

    event_logger.log(
        db=db,
        event_type="member_removed",
        event_category=EventLogger.CATEGORY_ROOM,
        success=True,
        user_id=current_user.id,
        event_metadata={"room_id": room_id, "removed_user_id": user_id},
        **client_info
    )
