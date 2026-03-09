"""Consent management endpoints for data privacy and compliance."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.models import ConsentLog, User
from backend.schemas import ConsentLogResponse, ConsentLogCreate
from backend.metrics import track_consent

router = APIRouter(prefix="/consent", tags=["consent"])


@router.post("", response_model=ConsentLogResponse, status_code=status.HTTP_201_CREATED)
async def create_consent_record(
    user_id: UUID,
    consent_scope: str,
    db: Session = Depends(get_db),
):
    """Create a consent record for user data processing.
    
    Records user consent before any AI analysis or data processing occurs.
    Supports multiple scopes: data_analysis, ai_advice, data_export, audit_review.
    
    Args:
        user_id: ID of user giving consent
        consent_scope: Scope of consent (data_analysis, ai_advice, data_export, audit_review)
        db: Database session
    
    Returns:
        ConsentLogResponse with consent record details
    
    Raises:
        HTTPException: 404 if user not found, 400 for invalid scope
    
    Example:
        POST /consent?user_id=123e4567-e89b-12d3-a456-426614174000&consent_scope=ai_advice
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Validate consent scope
    valid_scopes = ["data_analysis", "ai_advice", "data_export", "audit_review"]
    if consent_scope not in valid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid consent_scope. Must be one of: {', '.join(valid_scopes)}",
        )
    
    # Create consent record
    consent_log = ConsentLog(
        user_id=user_id,
        consent_scope=consent_scope,
        consent_timestamp=datetime.utcnow(),
        ip_address="",  # Could be populated from request headers
        user_agent="",  # Could be populated from request headers
    )
    
    db.add(consent_log)
    db.commit()
    db.refresh(consent_log)
    
    # Track metrics
    track_consent(scope=consent_scope, status="recorded")
    
    return ConsentLogResponse.from_orm(consent_log)


@router.get("/user/{user_id}", response_model=List[ConsentLogResponse])
async def get_user_consents(
    user_id: UUID,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get all consent records for a user.
    
    Args:
        user_id: User ID to fetch consents for
        limit: Maximum number of records to return (default 50)
        db: Database session
    
    Returns:
        List of ConsentLogResponse records
    
    Raises:
        HTTPException: 404 if user not found
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Get consent records ordered by most recent first
    consents = (
        db.query(ConsentLog)
        .filter(ConsentLog.user_id == user_id)
        .order_by(ConsentLog.consent_timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return [ConsentLogResponse.from_orm(c) for c in consents]


@router.get("/verify/{user_id}")
async def verify_consent(
    user_id: UUID,
    consent_scope: str,
    db: Session = Depends(get_db),
):
    """Verify that user has provided consent for a specific scope.
    
    Used by frontend/backend to enforce consent before operations.
    
    Args:
        user_id: User ID to check
        consent_scope: Scope to verify
        db: Database session
    
    Returns:
        {
            "has_consent": bool,
            "last_consent_at": datetime or null,
            "scope": str
        }
    
    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Find most recent consent for this scope
    recent_consent = (
        db.query(ConsentLog)
        .filter(
            ConsentLog.user_id == user_id,
            ConsentLog.consent_scope == consent_scope
        )
        .order_by(ConsentLog.consent_timestamp.desc())
        .first()
    )
    
    return {
        "has_consent": recent_consent is not None,
        "scope": consent_scope,
        "last_consent_at": recent_consent.consent_timestamp if recent_consent else None,
    }


@router.post("/withdraw/{user_id}")
async def withdraw_consent(
    user_id: UUID,
    consent_scope: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Withdraw user consent for a scope or all scopes.
    
    Creates an audit trail of consent withdrawal.
    Does NOT delete historical consent records (immutability).
    
    Args:
        user_id: User ID withdrawing consent
        consent_scope: Specific scope to withdraw, or null to withdraw all
        db: Database session
    
    Returns:
        {
            "withdrawn_scopes": list,
            "timestamp": datetime,
            "user_id": UUID
        }
    
    Raises:
        HTTPException: 404 if user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Determine scopes to withdraw
    if consent_scope:
        scopes_to_withdraw = [consent_scope]
    else:
        # Get all unique scopes the user has consented to
        scopes_to_withdraw = [
            row[0]
            for row in db.query(ConsentLog.consent_scope)
            .filter(ConsentLog.user_id == user_id)
            .distinct()
            .all()
        ]
    
    # Create withdrawal records for each scope
    for scope in scopes_to_withdraw:
        withdrawal = ConsentLog(
            user_id=user_id,
            consent_scope=scope,
            consent_timestamp=datetime.utcnow(),
            ip_address="",
            user_agent="",
            consent_status="withdrawn",  # Mark as withdrawal
        )
        db.add(withdrawal)
        track_consent(scope=scope, status="withdrawn")
    
    db.commit()
    
    return {
        "withdrawn_scopes": scopes_to_withdraw,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": str(user_id),
    }
