"""Financial report and analysis endpoints.

Provides financial analysis and reporting for user accounts.

Endpoints:
    GET /reports/{user_id} - Generate financial report for user
    GET /reports/{user_id}?assumptions=... - Generate report with custom assumptions
    GET /reports/{user_id}/spending-analysis - Get spending analysis only
    GET /reports/{user_id}/advanced-analysis - Get advanced spending analysis
"""

from datetime import datetime, date
from uuid import UUID
from typing import Optional, Dict, Any
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import User, FinancialSummary, Transaction, Goal, Holding
from backend.schemas import FinancialReportResponse, GoalSummary, PortfolioSummary
from backend.finance.report_builder import build_user_report
from decimal import Decimal

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{user_id}")
async def generate_financial_report(
    user_id: UUID,
    inflation_rate: Optional[float] = Query(None, ge=0, le=1, description="Inflation rate (0-1, e.g., 0.03 = 3%)"),
    discount_rate: Optional[float] = Query(None, ge=0, le=1, description="Discount rate for NPV calculations"),
    expected_equity_return: Optional[float] = Query(None, ge=0, le=1, description="Expected annual equity return"),
    expected_bond_return: Optional[float] = Query(None, ge=0, le=1, description="Expected annual bond return"),
    expected_cash_return: Optional[float] = Query(None, ge=0, le=1, description="Expected annual cash return"),
    db: Session = Depends(get_session),
):
    """
    Generate comprehensive financial report for user with optional custom assumptions.
    
    Analyzes income, expenses, savings, investments, and progress towards goals.
    Allows custom assumptions to be passed for scenario analysis.
    
    Args:
        user_id: User ID (required)
        inflation_rate: Optional inflation rate assumption (0-100%)
        discount_rate: Optional discount rate for NPV (0-100%)
        expected_equity_return: Optional expected stock return (0-100%)
        expected_bond_return: Optional expected bond return (0-100%)
        expected_cash_return: Optional expected cash return (0-100%)
        db: Database session
    
    Returns:
        Financial report with analysis summary
    
    Raises:
        HTTPException: 404 if user not found, 400 if assumptions invalid
    
    Examples:
        GET /reports/123e4567-e89b-12d3-a456-426614174000
        GET /reports/123e4567-e89b-12d3-a456-426614174000?expected_equity_return=0.10&inflation_rate=0.04
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Build assumptions dict from query parameters (only include non-None values)
    assumptions = {}
    if inflation_rate is not None:
        assumptions['inflation_rate'] = inflation_rate
    if discount_rate is not None:
        assumptions['discount_rate'] = discount_rate
    if expected_equity_return is not None:
        assumptions['expected_equity_return'] = expected_equity_return
    if expected_bond_return is not None:
        assumptions['expected_bond_return'] = expected_bond_return
    if expected_cash_return is not None:
        assumptions['expected_cash_return'] = expected_cash_return
    
    # Use build_user_report with (possibly empty) assumptions
    # Empty dict means defaults will be used
    try:
        report = build_user_report(user_id, db, assumptions=assumptions if assumptions else None)
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating report: {str(e)}",
        )


@router.get("/{user_id}/spending-analysis")
async def get_spending_analysis(
    user_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Get spending analysis for a user focusing on budget ratios, category distributions,
    and subscription detection.
    
    Analyzes transaction patterns to provide insights on:
    - Budget health (expense-to-income ratio)
    - Category-wise spending distribution
    - High spending alerts based on recommended percentages
    - Recurring subscription detection
    - Actionable recommendations for optimization
    
    Args:
        user_id: User ID (required)
        db: Database session
    
    Returns:
        Spending analysis with budget status, category breakdown, alerts, and recommendations
    
    Raises:
        HTTPException: 404 if user not found
    
    Examples:
        GET /reports/123e4567-e89b-12d3-a456-426614174000/spending-analysis
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    try:
        # Generate full report and extract spending analysis section
        report = build_user_report(user_id, db)
        spending_analysis = report.get('spending_analysis', {})
        return spending_analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating spending analysis: {str(e)}",
        )


@router.get("/{user_id}/advanced-analysis")
async def get_advanced_spending_analysis(
    user_id: UUID,
    db: Session = Depends(get_session),
):
    """
    Get advanced spending analysis with ML-powered insights.
    
    Provides comprehensive analysis including:
    - Seasonal spending pattern detection
    - Budget goal tracking & alerts
    - Month-over-month trend analysis
    - ML-powered saving recommendations
    - Peer anonymized benchmarking
    - Real-time spending alerts
    
    Args:
        user_id: User ID (required)
        db: Database session
    
    Returns:
        Advanced spending analysis with all metrics
    
    Raises:
        HTTPException: 404 if user not found
    
    Examples:
        GET /reports/123e4567-e89b-12d3-a456-426614174000/advanced-analysis
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    try:
        # Generate full report and extract advanced analysis section
        report = build_user_report(user_id, db)
        advanced_analysis = report.get('advanced_spending_analysis', {})
        return advanced_analysis
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating advanced analysis: {str(e)}",
        )
