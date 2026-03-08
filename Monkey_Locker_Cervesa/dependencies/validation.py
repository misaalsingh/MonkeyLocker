from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import Tuple
from services.db_connection import get_db
from models.users import User
from dependencies.auth import get_current_user


# async def get_room_or_404(
#     room_id: int = Path(..., description="Room ID"),
#     db: Session = Depends(get_db)
# ) -> 
    
#     if not room:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Room {room_id} not found"
#         )
    
#     return room


async def get_user_or_404(
    user_id: int = Path(..., description="User ID"),
    db: Session = Depends(get_db)
) -> User:
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    return user


# async def get_image_or_404(
#     image_id: int = Path(..., description="Image ID"),
#     db: Session = Depends(get_db)
# ) -> Image:
    
#     image = db.query(Image).filter(Image.id == image_id).first()
    
#     if not image:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Image {image_id} not found"
#         )
    
#     return image


# async def validate_room_membership(
#     room: Room = Depends(get_room_or_404),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ) -> Room:
    
#     is_member = db.query(RoomMember).filter(
#         RoomMember.room_id == room.id,
#         RoomMember.user_id == current_user.id
#     ).first()
    
#     if not is_member:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=f"You are not a member of room '{room.name}'"
#         )
    
#     return room


# async def validate_room_creator(
#     room: Room = Depends(get_room_or_404),
#     current_user: User = Depends(get_current_user)
# ) -> Room:
    
#     if room.created_by != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Only the room creator can perform this action"
#         )
    
#     return room


# async def validate_image_ownership(
#     image: Image = Depends(get_image_or_404),
#     current_user: User = Depends(get_current_user)
# ) -> Image:
    
#     if image.uploaded_by != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You can only delete your own images"
#         )
    
#     return image


# async def validate_image_room_access(
#     image: Image = Depends(get_image_or_404),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ) -> Image:
    
#     is_member = db.query(RoomMember).filter(
#         RoomMember.room_id == image.room_id,
#         RoomMember.user_id == current_user.id
#     ).first()
    
#     if not is_member:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You don't have access to this image"
#         )
    
#     return image


# async def get_room_with_membership(
#     room_id: int = Path(..., description="Room ID"),
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ) -> Tuple[Room, bool]:
    
#     room = db.query(Room).filter(Room.id == room_id).first()
    
#     if not room:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Room {room_id} not found"
#         )
    
#     is_member = db.query(RoomMember).filter(
#         RoomMember.room_id == room_id,
#         RoomMember.user_id == current_user.id
#     ).first() is not None
    
#     return room, is_member