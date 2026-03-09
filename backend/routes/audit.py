"""Audit log management endpoints for security and compliance review."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import AuditLog, User
from backend.schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["audit"])

# Simple API key auth for admin endpoints (should be replaced with proper OAuth in production)
ADMIN_API_KEY = "demo-admin-key-change-in-production"


def verify_admin_api_key(x_api_key: str = Header(None)):
    """Verify that request has valid admin API key."""
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing admin API key",
        )
    return True


@router.get("/recent", response_model=List[AuditLogResponse])
async def get_recent_audit_logs(
    limit: int = 100,
    offset: int = 0,
    event_type: Optional[str] = None,
    user_id: Optional[UUID] = None,
    admin: bool = Depends(verify_admin_api_key),
    db: Session = Depends(get_session),
):
    """Get recent audit log entries (admin only).
    
    Returns last N audit entries, optionally filtered by event type or user.
    Protected by API key authentication.
    
    Args:
        limit: Number of events to return (default 100, max 1000)
        offset: Number of events to skip for pagination (default 0)
        event_type: Optional filter by event type (ai_call, report_generated, etc.)
        user_id: Optional filter by user ID
        admin: Verified via API key check
        db: Database session
    
    Returns:
        List of AuditLogResponse records ordered by most recent first
    
    Raises:
        HTTPException: 403 if API key invalid
    
    Example:
        GET /audit/recent?limit=50&event_type=ai_call
        Headers: X-API-Key: demo-admin-key-change-in-production
    """
    # Validate limit
    limit = min(limit, 1000)  # Cap at 1000 for performance
    
    # Build query
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    
    # Apply filters
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    # Apply pagination
    entries = query.offset(offset).limit(limit).all()
    
    return [AuditLogResponse.from_orm(e) for e in entries]


@router.get("/user/{user_id}/history", response_model=List[AuditLogResponse])
async def get_user_audit_history(
    user_id: UUID,
    limit: int = 100,
    event_type: Optional[str] = None,
    admin: bool = Depends(verify_admin_api_key),
    db: Session = Depends(get_session),
):
    """Get audit history for a specific user (admin only).
    
    Returns all audit events related to a user, ordered by most recent first.
    
    Args:
        user_id: User ID to get history for
        limit: Maximum number of events to return (default 100)
        event_type: Optional filter by event type
        admin: Verified via API key check
        db: Database session
    
    Returns:
        List of AuditLogResponse for the user
    
    Raises:
        HTTPException: 403 if API key invalid, 404 if user not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Get audit entries
    query = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
    )
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    entries = query.limit(limit).all()
    
    return [AuditLogResponse.from_orm(e) for e in entries]


@router.get("/stats")
async def get_audit_stats(
    hours: int = 24,
    admin: bool = Depends(verify_admin_api_key),
    db: Session = Depends(get_session),
):
    """Get audit statistics for the past N hours (admin only).
    
    Returns count of events by type and status.
    
    Args:
        hours: Time window in hours (default 24)
        admin: Verified via API key check
        db: Database session
    
    Returns:
        {
            "time_window_hours": int,
            "total_events": int,
            "by_event_type": {event_type: count, ...},
            "by_resource_type": {resource_type: count, ...}
        }
    
    Raises:
        HTTPException: 403 if API key invalid
    """
    # Calculate time cutoff
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all events in window
    events = db.query(AuditLog).filter(AuditLog.created_at >= cutoff_time).all()
    
    # Count by event type
    event_type_counts = {}
    resource_type_counts = {}
    
    for event in events:
        event_type = event.event_type or "unknown"
        resource_type = event.resource_type or "unknown"
        
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        resource_type_counts[resource_type] = resource_type_counts.get(resource_type, 0) + 1
    
    return {
        "time_window_hours": hours,
        "total_events": len(events),
        "by_event_type": event_type_counts,
        "by_resource_type": resource_type_counts,
    }


@router.get("/ai-calls")
async def get_ai_call_audit(
    limit: int = 100,
    model_used: Optional[str] = None,
    blocked_only: bool = False,
    admin: bool = Depends(verify_admin_api_key),
    db: Session = Depends(get_session),
):
    """Get audit log of AI model calls (admin only).
    
    Returns audit events for AI advice generation, optionally filtered.
    
    Args:
        limit: Number of entries to return
        model_used: Filter by model (gemini, fallback, etc.)
        blocked_only: Show only blocked/filtered responses
        admin: Verified via API key check
        db: Database session
    
    Returns:
        List of AI call audit entries with details
    
    Raises:
        HTTPException: 403 if API key invalid
    """
    query = db.query(AuditLog).filter(AuditLog.event_type == "ai_call")
    
    if model_used:
        query = query.filter(AuditLog.resource_type == model_used)
    
    if blocked_only:
        # Assuming we store blocked status in details JSON
        query = query.filter(AuditLog.details.contains({"blocked": True}))
    
    entries = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return [AuditLogResponse.from_orm(e) for e in entries]
