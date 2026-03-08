# services/event_logger.py
from sqlalchemy.orm import Session
from models.events import Event
from typing import Optional, Dict, Any
from datetime import datetime


class EventLogger:
    """Enhanced event logging service with categories and better tracking"""
    
    # Event categories
    CATEGORY_AUTH = "auth"
    CATEGORY_USER = "user"
    CATEGORY_ROOM = "room"
    CATEGORY_IMAGE = "image"
    CATEGORY_SECURITY = "security"
    
    @staticmethod
    def log(
        db: Session,
        event_type: str,
        success: bool,
        event_category: Optional[str] = None,
        user_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        room_id: Optional[int] = None,
        image_id: Optional[int] = None,
        confidence_score: Optional[float] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Event:
        
        event = Event(
            event_type=event_type,
            event_category=event_category,
            success=success,
            user_id=user_id,
            target_user_id=target_user_id,
            room_id=room_id,
            image_id=image_id,
            confidence_score=confidence_score,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=event_metadata,
            error_message=error_message
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event
    
    @staticmethod
    def log_account_change(
        db: Session,
        event_type: str,
        user_id: int,
        changed_fields: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log account changes with field tracking"""
        
        return EventLogger.log(
            db=db,
            event_type=event_type,
            event_category=EventLogger.CATEGORY_USER,
            success=True,
            user_id=user_id,
            event_metadata={
                "changed_fields": changed_fields,
                "timestamp": datetime.utcnow().isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def log_security_event(
        db: Session,
        event_type: str,
        user_id: int,
        severity: str,
        description: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **kwargs
    ) -> Event:
        
        event_metadata = {
            "severity": severity,
            "description": description,
            **kwargs
        }
        
        return EventLogger.log(
            db=db,
            event_type=event_type,
            success=False,  # Security events are typically failures
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            event_metadata=event_metadata
        )
    
    @staticmethod
    def get_user_events(
        db: Session,
        user_id: int,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        query = db.query(Event).filter(Event.user_id == user_id)
        
        if event_type:
            query = query.filter(Event.event_type == event_type)
        
        events = query.order_by(Event.created_at.desc()).limit(limit).all()
        
        return events
    
    @staticmethod
    def get_failed_login_attempts(
        db: Session,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        hours: int = 24
    ) -> int:
        
        from datetime import timedelta
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(Event).filter(
            Event.event_type.in_(['login_attempt', 'face_login_attempt']),
            Event.success == False,
            Event.created_at >= since
        )
        
        if user_id:
            query = query.filter(Event.user_id == user_id)
        
        if ip_address:
            query = query.filter(Event.ip_address == ip_address)
        
        return query.count()
    
    @staticmethod
    def get_event_stats(
        db: Session,
        user_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        
        from datetime import timedelta
        from sqlalchemy import func
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(Event).filter(Event.created_at >= since)
        
        if user_id:
            query = query.filter(Event.user_id == user_id)
        
        # Total events
        total = query.count()
        
        # Successful vs failed
        successful = query.filter(Event.success == True).count()
        failed = query.filter(Event.success == False).count()
        
        # Events by type
        events_by_type = {}
        type_counts = db.query(
            Event.event_type,
            func.count(Event.id)
        ).filter(
            Event.created_at >= since
        )
        
        if user_id:
            type_counts = type_counts.filter(Event.user_id == user_id)
        
        type_counts = type_counts.group_by(Event.event_type).all()
        
        for event_type, count in type_counts:
            events_by_type[event_type] = count
        
        return {
            "period_days": days,
            "total_events": total,
            "successful_events": successful,
            "failed_events": failed,
            "success_rate": round((successful / total * 100) if total > 0 else 0, 2),
            "events_by_type": events_by_type
        }