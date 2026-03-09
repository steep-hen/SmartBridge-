"""Goal planning and strategy endpoints.

Provides goal planning analysis and savings strategies.

Endpoints:
    GET /goals/{user_id}/plan - Generate goal planning strategies for all goals
    GET /goals/{user_id}/plan/{goal_id} - Get strategy for specific goal
    POST /goals/{user_id}/plan - Create new goal with automatic strategy
"""

from uuid import UUID
from typing import Optional, Dict, Any
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import User, Goal, FinancialSummary
from backend.finance.goal_planner import generate_goal_strategy
from backend.finance.report_builder import _build_goal_planning

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/{user_id}/plan")
async def get_goal_planning_strategies(
    user_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Generate goal planning strategies for all active user goals.
    
    Analyzes each user goal and generates:
    - Required monthly SIP (Systematic Investment Plan)
    - Goal feasibility assessment
    - Actionable savings strategies
    - Timeline feasibility
    
    Args:
        user_id: User ID (required)
        db: Database session
    
    Returns:
        Dict with goal strategies and combined recommendations
    
    Raises:
        HTTPException: 404 if user not found, 400 if planning fails
    
    Response Structure:
        {
            'available': bool,
            'total_goals': int,
            'goal_strategies': [
                {
                    'goal': str,
                    'target_amount': float,
                    'required_monthly_sip': float,
                    'goal_feasibility': str,
                    'strategy': [str],
                    'action_items': [Dict],
                    'priority': str
                }
            ],
            'combined_recommendations': [str],
            'timestamp': str
        }
    
    Example:
        GET /goals/123e4567-e89b-12d3-a456-426614174000/plan
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    try:
        # Get latest financial summary
        latest_summary = (
            db.query(FinancialSummary)
            .filter(FinancialSummary.user_id == user_id)
            .order_by(FinancialSummary.year.desc(), FinancialSummary.month.desc())
            .first()
        )
        
        # Get all active goals
        goals = (
            db.query(Goal)
            .filter(Goal.user_id == user_id)
            .filter(Goal.status.in_(['ACTIVE', 'COMPLETED']))
            .all()
        )
        
        # Build goal planning using report builder helper
        goal_planning = _build_goal_planning(goals, latest_summary)
        
        return goal_planning
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating goal planning strategies: {str(e)}",
        )


@router.get("/{user_id}/plan/{goal_id}")
async def get_goal_strategy(
    user_id: UUID,
    goal_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Get detailed strategy plan for a specific goal.
    
    Analyzes individual goal and provides:
    - Required monthly SIP calculation
    - Complete feasibility assessment
    - Detailed action items with impact estimates
    - Timeline analysis
    
    Args:
        user_id: User ID (required)
        goal_id: Goal ID (required)
        db: Database session
    
    Returns:
        Detailed strategy for single goal
    
    Raises:
        HTTPException: 404 if user/goal not found, 400 if planning fails
    
    Response Structure:
        {
            'available': bool,
            'goal': str,
            'target_amount': float,
            'current_savings': float,
            'years_to_achieve': int,
            'required_monthly_sip': float,
            'goal_feasibility': str,
            'feasibility_color': str,
            'monthly_income': float,
            'monthly_expenses': float,
            'surplus_monthly': float,
            'strategy': [str],
            'action_items': [
                {
                    'action': str,
                    'category': str,
                    'estimated_impact': float | str,
                    'priority': str,
                    'difficulty': str,
                    'timeline': str
                }
            ],
            'priority': str,
            'timestamp': str
        }
    
    Example:
        GET /goals/123e4567-e89b-12d3-a456-426614174000/plan/abc12345-e89b-12d3-a456-426614174001
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Verify goal exists and belongs to user
    goal = (
        db.query(Goal)
        .filter(Goal.id == goal_id)
        .filter(Goal.user_id == user_id)
        .first()
    )
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal with ID '{goal_id}' not found for user",
        )
    
    try:
        # Get latest financial summary
        latest_summary = (
            db.query(FinancialSummary)
            .filter(FinancialSummary.user_id == user_id)
            .order_by(FinancialSummary.year.desc(), FinancialSummary.month.desc())
            .first()
        )
        
        if not latest_summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no financial summary. Please add financial data first.",
            )
        
        # Calculate years to goal
        years = 1
        if goal.target_date:
            today = date.today()
            delta = goal.target_date - today
            years = max(1, (delta.days // 365) + 1)
        
        # Calculate monthly income and expenses
        monthly_income = float(latest_summary.total_income) / max(latest_summary.month, 1)
        monthly_expenses = float(latest_summary.total_expenses) / max(latest_summary.month, 1)
        
        # Generate strategy for this goal
        strategy = generate_goal_strategy(
            goal_name=goal.goal_name,
            target_amount=float(goal.target_amount),
            current_savings=float(goal.current_amount or 0.0),
            years=years,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            expected_return=0.08,  # 8% default annual return
        )
        
        return strategy
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating goal strategy: {str(e)}",
        )


@router.post("/{user_id}/plan/create")
async def create_goal_with_strategy(
    user_id: UUID,
    goal_name: str,
    target_amount: float,
    target_date: Optional[str] = None,
    db: Session = Depends(get_session),
):
    """
    Create new goal and immediately generate strategy.
    
    Creates a new goal for user and generates a comprehensive strategy
    showing feasibility, required savings, and action steps.
    
    Args:
        user_id: User ID (required)
        goal_name: Name of the goal (e.g., "Buy House")
        target_amount: Target amount in rupees
        target_date: Optional target date (YYYY-MM-DD format)
        db: Database session
    
    Returns:
        New goal with generated strategy
    
    Raises:
        HTTPException: 404 if user not found, 400 if creation/planning fails
    
    Example:
        POST /goals/123e4567-e89b-12d3-a456-426614174000/plan/create
        Body: {
            "goal_name": "Buy House",
            "target_amount": 5000000,
            "target_date": "2035-12-31"
        }
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    if target_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target amount must be greater than 0",
        )
    
    try:
        # Get latest financial summary
        latest_summary = (
            db.query(FinancialSummary)
            .filter(FinancialSummary.user_id == user_id)
            .order_by(FinancialSummary.year.desc(), FinancialSummary.month.desc())
            .first()
        )
        
        if not latest_summary:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no financial summary. Please add financial data first.",
            )
        
        # Parse target date if provided
        goal_target_date = None
        years = 1
        if target_date:
            try:
                goal_target_date = date.fromisoformat(target_date)
                today = date.today()
                delta = goal_target_date - today
                years = max(1, (delta.days // 365) + 1)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )
        
        # Create new goal
        new_goal = Goal(
            user_id=user_id,
            goal_name=goal_name,
            goal_type="INVESTMENT",
            target_amount=float(target_amount),
            current_amount=0.0,
            target_date=goal_target_date,
            status="ACTIVE",
            priority="MEDIUM",
        )
        
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        
        # Generate strategy for new goal
        monthly_income = float(latest_summary.total_income) / max(latest_summary.month, 1)
        monthly_expenses = float(latest_summary.total_expenses) / max(latest_summary.month, 1)
        
        strategy = generate_goal_strategy(
            goal_name=goal_name,
            target_amount=target_amount,
            current_savings=0.0,
            years=years,
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
            expected_return=0.08,
        )
        
        return {
            'goal_id': str(new_goal.id),
            'goal': new_goal.goal_name,
            'created_at': new_goal.created_at.isoformat(),
            'strategy': strategy,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating goal with strategy: {str(e)}",
        )
