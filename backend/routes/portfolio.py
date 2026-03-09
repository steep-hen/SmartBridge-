"""Portfolio recommendation endpoints.

Provides portfolio allocation recommendations and asset class guidance.

Endpoints:
    GET /portfolio/recommendation/{user_id} - Get portfolio recommendation for user
    POST /portfolio/recommendation/{user_id} - Generate custom recommendation
"""

from uuid import UUID
from typing import Optional, Dict, Any
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.db import get_session
from backend.models import User, FinancialSummary, Holding
from backend.finance.portfolio_optimizer import (
    generate_portfolio_recommendation,
    calculate_portfolio_value_at_horizon,
    get_risk_adjusted_recommendation,
)
from backend.finance.report_builder import _round_currency

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/recommendation/{user_id}")
async def get_portfolio_recommendation(
    user_id: UUID,
    risk_tolerance: Optional[str] = Query(
        None,
        description="Risk profile: 'low', 'medium', or 'high'. If not provided, defaults to medium."
    ),
    include_projection: Optional[bool] = Query(
        True,
        description="Include portfolio value projection"
    ),
    db: Session = Depends(get_session),
):
    """
    Get portfolio allocation recommendation for user.
    
    Returns recommended asset allocation (equity, debt, gold) with specific
    instrument recommendations based on user's risk tolerance and profile.
    
    Args:
        user_id: User ID (required)
        risk_tolerance: Optional override for risk profile ('low', 'medium', 'high')
        include_projection: Whether to include future value projection (default: True)
        db: Database session
    
    Returns:
        Portfolio recommendation with allocation percentages and instruments
    
    Raises:
        HTTPException: 404 if user not found, 400 if risk_tolerance invalid
    
    Examples:
        GET /portfolio/recommendation/123e4567-e89b-12d3-a456-426614174000
        GET /portfolio/recommendation/123e4567-e89b-12d3-a456-426614174000?risk_tolerance=high
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Determine age from date of birth
    age = None
    if user.date_of_birth:
        today = date.today()
        age = today.year - user.date_of_birth.year - (
            (today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day)
        )
    
    # Get financial summary for investment capacity
    summary = (
        db.query(FinancialSummary)
        .filter(FinancialSummary.user_id == user_id)
        .order_by(FinancialSummary.year.desc(), FinancialSummary.month.desc())
        .first()
    )
    
    monthly_investment = None
    if summary:
        monthly_income = float(summary.total_income) / max(summary.month, 1)
        monthly_expenses = float(summary.total_expenses) / max(summary.month, 1)
        monthly_investment = max(monthly_income - monthly_expenses, 0)
    
    # Use provided risk_tolerance or default to medium
    if not risk_tolerance:
        risk_tolerance = 'medium'
    
    # Validate risk_tolerance
    if risk_tolerance not in ['low', 'medium', 'high']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid risk_tolerance '{risk_tolerance}'. Must be 'low', 'medium', or 'high'"
        )
    
    try:
        # Generate recommendation
        recommendation = generate_portfolio_recommendation(
            risk_tolerance=risk_tolerance,
            age=age,
            monthly_investment=monthly_investment,
        )
        
        # Add current holdings info
        holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
        recommendation['current_holdings'] = {
            'count': len(holdings),
            'total_value': _round_currency(sum(float(h.current_value or 0) for h in holdings)),
        }
        
        # Add projection if requested and we have investment capacity
        if include_projection and monthly_investment and monthly_investment > 0:
            projection = calculate_portfolio_value_at_horizon(
                initial_investment=max(float(summary.total_investments or 0), 0) if summary else 0,
                monthly_sip=monthly_investment,
                allocation=recommendation['recommended_portfolio'],
                investment_horizon=20,  # Default 20 year horizon
            )
            recommendation['20year_projection'] = projection
        
        return {
            'available': True,
            'user_id': str(user_id),
            'recommendation': recommendation,
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating recommendation: {str(e)}"
        )


@router.post("/recommendation/{user_id}")
async def create_custom_recommendation(
    user_id: UUID,
    risk_tolerance: str = Query(
        "medium",
        description="Risk profile: 'low', 'medium', or 'high'"
    ),
    investment_horizon: Optional[int] = Query(
        None,
        ge=1,
        le=50,
        description="Investment horizon in years (1-50)"
    ),
    monthly_investment: Optional[float] = Query(
        None,
        ge=0,
        description="Planned monthly investment amount in rupees"
    ),
    db: Session = Depends(get_session),
):
    """
    Generate custom portfolio recommendation with specific parameters.
    
    Allows custom specification of risk tolerance, investment horizon,
    and monthly investment amount for scenario analysis.
    
    Args:
        user_id: User ID (required)
        risk_tolerance: Risk profile ('low', 'medium', 'high') (default: medium)
        investment_horizon: Years until funds needed (optional, 1-50)
        monthly_investment: Planned monthly SIP amount (optional)
        db: Database session
    
    Returns:
        Customized portfolio recommendation
    
    Raises:
        HTTPException: 404 if user not found, 400 if parameters invalid
    
    Examples:
        POST /portfolio/recommendation/user-id?risk_tolerance=high&investment_horizon=15&monthly_investment=10000
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Validate risk_tolerance
    if risk_tolerance not in ['low', 'medium', 'high']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid risk_tolerance '{risk_tolerance}'. Must be 'low', 'medium', or 'high'"
        )
    
    try:
        # Get age from user profile
        age = None
        if user.date_of_birth:
            today = date.today()
            age = today.year - user.date_of_birth.year - (
                (today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day)
            )
        
        # Generate custom recommendation
        recommendation = generate_portfolio_recommendation(
            risk_tolerance=risk_tolerance,
            age=age,
            investment_horizon=investment_horizon,
            monthly_investment=monthly_investment,
        )
        
        # Add projection if monthly investment provided
        if monthly_investment and monthly_investment > 0 and investment_horizon:
            projection = calculate_portfolio_value_at_horizon(
                initial_investment=0,
                monthly_sip=monthly_investment,
                allocation=recommendation['recommended_portfolio'],
                investment_horizon=investment_horizon,
            )
            recommendation['custom_projection'] = projection
        
        return {
            'available': True,
            'user_id': str(user_id),
            'parameters': {
                'risk_tolerance': risk_tolerance,
                'investment_horizon': investment_horizon,
                'monthly_investment': monthly_investment,
            },
            'recommendation': recommendation,
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error generating recommendation: {str(e)}"
        )


@router.get("/instruments/{asset_class}")
async def get_asset_class_instruments(
    asset_class: str = Query(
        "equity",
        description="Asset class: 'equity', 'debt', or 'gold'"
    ),
    time_horizon: Optional[str] = Query(
        "medium_term",
        description="Time horizon: 'short_term' (1-5y), 'medium_term' (5-10y), 'long_term' (10+y)"
    ),
):
    """
    Get recommended instruments for specific asset class and time horizon.
    
    Returns list of recommended mutual funds, ETFs, and direct instruments
    for the specified asset class.
    
    Args:
        asset_class: Which asset class ('equity', 'debt', 'gold')
        time_horizon: Investment timeline ('short_term', 'medium_term', 'long_term')
    
    Returns:
        List of recommended instruments with details
    
    Raises:
        HTTPException: 400 if parameters invalid
    
    Examples:
        GET /portfolio/instruments/equity?time_horizon=long_term
        GET /portfolio/instruments/debt?time_horizon=short_term
    """
    from backend.finance.portfolio_optimizer import INSTRUMENT_RECOMMENDATIONS
    
    # Validate inputs
    valid_classes = list(INSTRUMENT_RECOMMENDATIONS.keys())
    if asset_class not in valid_classes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset_class '{asset_class}'. Must be one of: {valid_classes}"
        )
    
    if asset_class == 'equity':
        valid_horizons = ['short_term', 'medium_term', 'long_term']
        if time_horizon not in valid_horizons:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time_horizon '{time_horizon}'. Must be one of: {valid_horizons}"
            )
        instruments = INSTRUMENT_RECOMMENDATIONS['equity'].get(
            time_horizon,
            INSTRUMENT_RECOMMENDATIONS['equity']['medium_term']
        )
    else:
        # Debt and gold have sub-categories
        instruments = []
        if asset_class == 'debt':
            for category_instruments in INSTRUMENT_RECOMMENDATIONS['debt'].values():
                instruments.extend(category_instruments)
        elif asset_class == 'gold':
            for category_instruments in INSTRUMENT_RECOMMENDATIONS['gold'].values():
                instruments.extend(category_instruments)
    
    return {
        'asset_class': asset_class,
        'time_horizon': time_horizon if asset_class == 'equity' else 'N/A',
        'count': len(instruments),
        'instruments': instruments,
    }


@router.post("/projection")
async def calculate_projection(
    initial_amount: float = Query(..., ge=0, description="Initial investment in rupees"),
    monthly_sip: float = Query(..., ge=0, description="Monthly SIP amount in rupees"),
    equity_percent: int = Query(70, ge=0, le=100, description="Equity allocation %"),
    debt_percent: int = Query(20, ge=0, le=100, description="Debt allocation %"),
    gold_percent: int = Query(10, ge=0, le=100, description="Gold allocation %"),
    years: int = Query(10, ge=1, le=50, description="Investment horizon in years"),
):
    """
    Calculate projected portfolio value for custom allocation.
    
    Projects the future value of portfolio based on allocation and returns.
    
    Args:
        initial_amount: Starting investment (₹)
        monthly_sip: Monthly contribution (₹)
        equity_percent: Equity allocation (0-100%)
        debt_percent: Debt allocation (0-100%)
        gold_percent: Gold allocation (0-100%)
        years: Investment horizon (1-50 years)
    
    Returns:
        Projected portfolio value and metrics
    
    Raises:
        HTTPException: 400 if allocation percentages invalid
    
    Examples:
        POST /portfolio/projection?initial_amount=100000&monthly_sip=5000&years=20
    """
    # Validate allocation percentages sum to 100
    total_percent = equity_percent + debt_percent + gold_percent
    if total_percent != 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allocation percentages must sum to 100. Got: {total_percent}% "
                  f"(equity: {equity_percent}, debt: {debt_percent}, gold: {gold_percent})"
        )
    
    if years <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Investment horizon must be positive"
        )
    
    try:
        allocation = {
            'equity': equity_percent,
            'debt': debt_percent,
            'gold': gold_percent,
        }
        
        projection = calculate_portfolio_value_at_horizon(
            initial_investment=initial_amount,
            monthly_sip=monthly_sip,
            allocation=allocation,
            investment_horizon=years,
        )
        
        return {
            'parameters': {
                'initial_amount': initial_amount,
                'monthly_sip': monthly_sip,
                'allocation': allocation,
                'investment_horizon_years': years,
            },
            'projection': projection,
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error calculating projection: {str(e)}"
        )
