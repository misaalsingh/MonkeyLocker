from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class EventCreate(BaseModel):
    user_id: Optional[int] = None
    room_id: Optional[int] = None
    event_type: str
    status: Optional[str] = None
    confidence_score: Optional[float] = None
    event_metadata: Optional[Dict[str, Any]] = None


class EventRead(BaseModel):
    id: int
    user_id: Optional[int]
    room_id: Optional[int]
    event_type: str
    status: Optional[str]
    confidence_score: Optional[float]
    event_metadata: Optional[Dict[str, Any]]
    created_at: datetime