"""User management endpoints.

Provides CRUD operations for user accounts and profiles.

Endpoints:
    GET  /users - List all users (paginated)
    POST /users - Create new user
    GET  /users/{user_id} - Get user profile with financial data
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import User, FinancialSummary, Holding, Goal
from backend.schemas import (
    UserCreate,
    UserResponse,
    UserDetailResponse,
    FinancialSummaryResponse,
    HoldingResponse,
    GoalResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_session),
):
    """
    List all users with pagination.
    
    Args:
        skip: Number of records to skip (default: 0)
        limit: Number of records to return (default: 20, max: 100)
        db: Database session
    
    Returns:
        List of user records
    
    Example:
        GET /users?skip=0&limit=20
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_session),
):
    """
    Create a new user account.
    
    Args:
        user_data: User creation request data
        db: Database session
    
    Returns:
        Created user record
    
    Raises:
        HTTPException: 400 if email already exists
    
    Example:
        POST /users
        {
            "email": "john@example.com",
            "name": "John Doe"
        }
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{user_data.email}' already exists",
        )
    
    # Create new user
    db_user = User(**user_data.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Get user profile with financial data.
    
    Returns user with latest financial summary, holdings, and goals.
    
    Args:
        user_id: User ID (UUID)
        db: Database session
    
    Returns:
        User profile with financial data
    
    Raises:
        HTTPException: 404 if user not found
    
    Example:
        GET /users/123e4567-e89b-12d3-a456-426614174000
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Eagerly load relationships
    db.refresh(user)
    
    return user


@router.get("/{user_id}/transactions", response_model=dict)
async def get_user_transactions(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    month: Optional[str] = Query(None, description="Filter by month (YYYY-MM)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_session),
):
    """
    Get user transactions with pagination and filtering.
    
    Args:
        user_id: User ID
        skip: Records to skip
        limit: Records to return
        month: Optional month filter (YYYY-MM format)
        category: Optional category filter
        db: Database session
    
    Returns:
        Paginated transaction list with metadata
    
    Raises:
        HTTPException: 404 if user not found
    """
    from backend.models import Transaction
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Build query
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    
    # Apply filters
    if month:
        try:
            year, month_num = map(int, month.split("-"))
            from datetime import date
            query = query.filter(
                Transaction.transaction_date >= date(year, month_num, 1),
                Transaction.transaction_date < (
                    date(year, month_num + 1, 1) if month_num < 12 else date(year + 1, 1, 1)
                ),
            )
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid month format. Use YYYY-MM",
            )
    
    if category:
        query = query.filter(Transaction.category == category)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    transactions = query.offset(skip).limit(limit).all()
    
    return {
        "items": [
            {
                "id": str(t.id),
                "date": t.transaction_date,
                "amount": float(t.amount),
                "category": t.category,
                "merchant": t.merchant_name,
                "type": t.transaction_type,
                "recurring": t.is_recurring,
            }
            for t in transactions
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }
