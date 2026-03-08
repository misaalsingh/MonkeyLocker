from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from services.db_connection import get_db
from models.events import Event
from models.users import User
from schemas.events import EventRead
from dependencies.auth import get_current_user
from dependencies.pagination import PaginationParams, DateRangeParams
from services.event_logger import EventLogger

router = APIRouter()
event_logger = EventLogger()


@router.get("/", response_model=List[EventRead])
def list_my_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    days: int = Query(7, ge=1, le=365, description="Number of days to look back"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    # Base query - only user's own events
    query = db.query(Event).filter(Event.user_id == current_user.id)
    
    # Apply filters
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if success is not None:
        query = query.filter(Event.success == success)
    
    # Filter by date range
    since = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Event.created_at >= since)
    
    # Order and paginate
    events = query.order_by(
        Event.created_at.desc()
    ).offset(pagination.skip).limit(pagination.limit).all()
    
    return events


@router.get("/all-types", response_model=List[str])
def list_event_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    event_types = db.query(Event.event_type).filter(
        Event.user_id == current_user.id
    ).distinct().all()
    
    return [et[0] for et in event_types]


@router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own events"
        )
    
    return event

@router.get("/stats/summary")
def get_my_event_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days for stats"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    from sqlalchemy import func
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Total events
    total = db.query(func.count(Event.id)).filter(
        Event.user_id == current_user.id,
        Event.created_at >= since
    ).scalar()
    
    # Successful events
    successful = db.query(func.count(Event.id)).filter(
        Event.user_id == current_user.id,
        Event.success == True,
        Event.created_at >= since
    ).scalar()
    
    # Failed events
    failed = db.query(func.count(Event.id)).filter(
        Event.user_id == current_user.id,
        Event.success == False,
        Event.created_at >= since
    ).scalar()
    
    # Events by type
    events_by_type = {}
    event_types = db.query(
        Event.event_type,
        func.count(Event.id)
    ).filter(
        Event.user_id == current_user.id,
        Event.created_at >= since
    ).group_by(Event.event_type).all()
    
    for event_type, count in event_types:
        events_by_type[event_type] = count
    
    # Recent failed login attempts
    recent_failures = db.query(Event).filter(
        Event.user_id == current_user.id,
        Event.event_type.in_(['login_attempt', 'face_login_attempt']),
        Event.success == False,
        Event.created_at >= since
    ).order_by(Event.created_at.desc()).limit(5).all()
    
    return {
        "period_days": days,
        "total_events": total or 0,
        "successful_events": successful or 0,
        "failed_events": failed or 0,
        "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
        "events_by_type": events_by_type,
        "recent_failures": [
            {
                "event_type": e.event_type,
                "created_at": e.created_at,
                "ip_address": e.ip_address
            }
            for e in recent_failures
        ]
    }


@router.get("/stats/security-alerts")
def get_security_alerts(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    
    since = datetime.utcnow() - timedelta(days=days)
    
    failed_logins = event_logger.get_failed_login_attempts(
        db=db,
        user_id=current_user.id,
        hours=days * 24
    )
    
    failed_ips = db.query(Event.ip_address).filter(
        Event.user_id == current_user.id,
        Event.event_type.in_(['login_attempt', 'face_login_attempt']),
        Event.success == False,
        Event.created_at >= since,
        Event.ip_address.isnot(None)
    ).distinct().all()
    
    alerts = []
    
    if failed_logins > 5:
        alerts.append({
            "severity": "high",
            "type": "multiple_failed_logins",
            "message": f"{failed_logins} failed login attempts in the last {days} days",
            "count": failed_logins
        })
    
    if len(failed_ips) > 3:
        alerts.append({
            "severity": "medium",
            "type": "multiple_ip_addresses",
            "message": f"Login attempts from {len(failed_ips)} different IP addresses",
            "count": len(failed_ips)
        })
    
    return {
        "alerts": alerts,
        "failed_login_count": failed_logins,
        "unique_ips_count": len(failed_ips)
    }


@router.get("/stats/activity-timeline")
def get_activity_timeline(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    from sqlalchemy import func, cast, Date
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Group events by date
    daily_activity = db.query(
        cast(Event.created_at, Date).label('date'),
        func.count(Event.id).label('count')
    ).filter(
        Event.user_id == current_user.id,
        Event.created_at >= since
    ).group_by(cast(Event.created_at, Date)).order_by(
        cast(Event.created_at, Date)
    ).all()
    
    return {
        "period_days": days,
        "timeline": [
            {
                "date": str(date),
                "count": count
            }
            for date, count in daily_activity
        ]
    }