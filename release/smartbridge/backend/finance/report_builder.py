"""Financial report builder - queries DB and constructs comprehensive JSON reports.

Builds a user's financial report by:
1. Querying latest user profile, financial summary, holdings, and goals
2. Computing financial metrics using engine.py
3. Projecting goal achievement
4. Combining into structured JSON for AI analysis and API responses

All calculations are deterministic. Same user state always produces same report.
"""

from datetime import datetime, date
from typing import Dict, Optional, List, Any
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.models import (
    User, FinancialSummary, Holding, Goal, Transaction, MarketPrice
)
from backend.finance.engine import (
    compute_savings_rate,
    compute_debt_to_income_ratio,
    compute_emergency_fund_months,
    compute_required_sip,
    project_investment_growth,
    compute_financial_health_score,
    compute_goal_metrics,
    _round_currency,
    _round_ratio,
)


# ============================================================================
# REPORT BUILDER MAIN FUNCTION
# ============================================================================

def build_user_report(
    user_id: UUID,
    db: Session,
    assumptions: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Build comprehensive financial report for user.
    
    Queries database for user's financial state and computes all metrics,
    projections, and health scores.
    
    Args:
        user_id: ID of user to analyze
        db: SQLAlchemy session
        assumptions: Optional dict with keys:
            - inflation_rate: float (default: 0.03 = 3%)
            - discount_rate: float (default: 0.05 = 5%)
            - expected_equity_return: float (default: 0.07 = 7% annual)
            - expected_bond_return: float (default: 0.04 = 4% annual)
            - expected_cash_return: float (default: 0.02 = 2% annual)
            
    Returns:
        dict with keys:
            - user_profile: User basic info
            - financial_snapshot: Latest monthly snapshot
            - computed_metrics: Health, savings, debt, emergency fund
            - holdings_summary: Portfolio snapshot with allocation
            - goals_analysis: Array of goals with projections
            - overall_health_score: 0-100
            - assumptions_used: Parameters used in calculations
            - report_generated_at: ISO timestamp
            
    Raises:
        ValueError: If user not found
        
    Notes:
        - Returns empty/zero values if user has no financial data
        - Projections use expected returns from assumptions
        - All monetary values rounded to 2 decimals
    """
    # Default assumptions
    if assumptions is None:
        assumptions = {}
    
    default_assumptions = {
        'inflation_rate': 0.03,
        'discount_rate': 0.05,
        'expected_equity_return': 0.07,
        'expected_bond_return': 0.04,
        'expected_cash_return': 0.02,
    }
    default_assumptions.update(assumptions)
    assumptions = default_assumptions
    
    # ---- FETCH DATA FROM DATABASE ----
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    # Latest financial summary
    latest_summary = (
        db.query(FinancialSummary)
        .filter(FinancialSummary.user_id == user_id)
        .order_by(FinancialSummary.year.desc(), FinancialSummary.month.desc())
        .first()
    )
    
    # Holdings
    holdings = (
        db.query(Holding)
        .filter(Holding.user_id == user_id)
        .all()
    )
    
    # Goals
    goals = (
        db.query(Goal)
        .filter(Goal.user_id == user_id)
        .filter(Goal.status.in_(['ACTIVE', 'COMPLETED']))
        .all()
    )
    
    # All transactions (for debt estimation at least)
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )
    
    # ---- BUILD REPORT SECTIONS ----
    
    user_profile = _build_user_profile(user)
    
    financial_snapshot = _build_financial_snapshot(latest_summary)
    
    computed_metrics = _compute_metrics(
        latest_summary, holdings, transactions
    )
    
    holdings_summary = _build_holdings_summary(holdings)
    
    goals_analysis = _build_goals_analysis(
        goals, latest_summary, assumptions
    )
    
    overall_health = compute_financial_health_score(computed_metrics)
    
    # ---- ASSEMBLE REPORT ----
    
    report = {
        'report_id': f"{user_id}_{datetime.utcnow().isoformat()}",
        'report_generated_at': datetime.utcnow().isoformat(),
        'user_profile': user_profile,
        'financial_snapshot': financial_snapshot,
        'computed_metrics': computed_metrics,
        'holdings_summary': holdings_summary,
        'goals_analysis': goals_analysis,
        'overall_health_score': overall_health,
        'assumptions_used': assumptions,
    }
    
    return report


# ============================================================================
# REPORT BUILDER HELPERS
# ============================================================================

def _build_user_profile(user: User) -> Dict[str, Any]:
    """Extract user basic profile info."""
    return {
        'user_id': str(user.id),
        'email': user.email,
        'name': user.name,
        'country': user.country,
        'gender': user.gender,
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'member_since': user.created_at.isoformat(),
    }


def _build_financial_snapshot(summary: Optional[FinancialSummary]) -> Dict[str, Any]:
    """Build latest financial snapshot section."""
    if not summary:
        return {
            'available': False,
            'period': None,
            'total_income': 0.0,
            'total_expenses': 0.0,
            'total_savings': 0.0,
            'total_investments': 0.0,
            'net_worth': 0.0,
            'last_updated': None,
        }
    
    return {
        'available': True,
        'period': f"{summary.year}-{summary.month:02d}",
        'total_income': _round_currency(float(summary.total_income)),
        'total_expenses': _round_currency(float(summary.total_expenses)),
        'total_savings': _round_currency(float(summary.total_savings)),
        'total_investments': _round_currency(float(summary.total_investments)),
        'net_worth': _round_currency(float(summary.net_worth)),
        'last_updated': summary.updated_at.isoformat(),
    }


def _compute_metrics(
    summary: Optional[FinancialSummary],
    holdings: List[Holding],
    transactions: List[Transaction],
) -> Dict[str, float]:
    """Compute all key financial metrics."""
    
    if not summary:
        return {
            'savings_rate': 0.0,
            'debt_to_income_ratio': 0.0,
            'emergency_fund_months': 0.0,
            'investment_ratio': 0.0,
            'monthly_income': 0.0,
            'monthly_expenses': 0.0,
            'monthly_savings': 0.0,
        }
    
    monthly_income = float(summary.total_income) / (summary.month or 1)
    monthly_expenses = float(summary.total_expenses) / (summary.month or 1)
    monthly_savings = float(summary.total_savings) / (summary.month or 1)
    
    # Estimate total debt from recent transactions marked as debt
    # (simplified: could enhance with explicit debt tracking)
    total_debt = 0.0
    
    # Calculate investment ratio
    total_net_worth = float(summary.net_worth)
    total_investments = float(summary.total_investments)
    investment_ratio = (
        total_investments / total_net_worth
        if total_net_worth > 0
        else 0.0
    )
    
    savings_rate = compute_savings_rate(monthly_income, monthly_savings)
    dti = compute_debt_to_income_ratio(total_debt, monthly_income)
    emergency_months = compute_emergency_fund_months(
        float(summary.total_savings), monthly_expenses
    )
    
    return {
        'savings_rate': _round_ratio(savings_rate, places=2),
        'debt_to_income_ratio': _round_ratio(dti, places=4),
        'emergency_fund_months': _round_ratio(emergency_months, places=2),
        'investment_ratio': _round_ratio(investment_ratio, places=4),
        'monthly_income': _round_currency(monthly_income),
        'monthly_expenses': _round_currency(monthly_expenses),
        'monthly_savings': _round_currency(monthly_savings),
    }


def _build_holdings_summary(holdings: List[Holding]) -> Dict[str, Any]:
    """Build investment holdings summary."""
    if not holdings:
        return {
            'count': 0,
            'total_cost_basis': 0.0,
            'total_current_value': 0.0,
            'total_unrealized_gain_loss': 0.0,
            'gain_loss_percentage': 0.0,
            'holdings': [],
        }
    
    total_cost = 0.0
    total_value = 0.0
    holdings_detail = []
    
    for holding in holdings:
        cost = float(holding.quantity) * float(holding.average_cost)
        value = float(holding.current_value or 0.0)
        
        total_cost += cost
        total_value += value
        
        gain_loss = value - cost
        gain_loss_pct = (gain_loss / cost * 100) if cost > 0 else 0.0
        
        holdings_detail.append({
            'ticker': holding.ticker,
            'asset_type': holding.asset_type,
            'quantity': _round_ratio(float(holding.quantity), places=8),
            'average_cost_per_unit': _round_currency(float(holding.average_cost)),
            'total_cost': _round_currency(cost),
            'current_value': _round_currency(value),
            'unrealized_gain_loss': _round_currency(gain_loss),
            'gain_loss_percentage': _round_ratio(gain_loss_pct, places=2),
        })
    
    total_gain_loss = total_value - total_cost
    total_gain_loss_pct = (
        total_gain_loss / total_cost * 100 if total_cost > 0 else 0.0
    )
    
    return {
        'count': len(holdings),
        'total_cost_basis': _round_currency(total_cost),
        'total_current_value': _round_currency(total_value),
        'total_unrealized_gain_loss': _round_currency(total_gain_loss),
        'gain_loss_percentage': _round_ratio(total_gain_loss_pct, places=2),
        'holdings': holdings_detail,
    }


def _build_goals_analysis(
    goals: List[Goal],
    summary: Optional[FinancialSummary],
    assumptions: Dict[str, float],
) -> Dict[str, Any]:
    """Build goals analysis with projections."""
    if not goals:
        return {
            'count': 0,
            'goals': [],
            'achievement_summary': {
                'achievable_count': 0,
                'total_goals': 0,
                'total_progress_percentage': 0.0,
            }
        }
    
    goals_detail = []
    achievable_count = 0
    total_progress = 0.0
    
    for goal in goals:
        # Estimate months remaining
        months_remaining = 12  # Default 1 year
        if goal.target_date:
            today = date.today()
            delta = goal.target_date - today
            months_remaining = max(1, delta.days // 30)
        
        # Determine appropriate return rate based on goal type
        expected_return = assumptions.get('expected_equity_return', 0.07)
        if goal.goal_type and 'SAVINGS' in goal.goal_type.upper():
            expected_return = assumptions.get('expected_cash_return', 0.02)
        
        # Compute metrics for this goal
        metrics = compute_goal_metrics(
            goal_target=float(goal.target_amount),
            goal_current=float(goal.current_amount),
            goal_monthly_increment=0.0,  # No planned increment in basic model
            months_remaining=months_remaining,
            expected_annual_return=expected_return,
        )
        
        # Build projection sample (10 samples across time horizon)
        sample_months = [0, months_remaining // 4, months_remaining // 2, 
                        (3 * months_remaining) // 4, months_remaining]
        sample_months = [m for m in sample_months if 0 <= m <= months_remaining]
        sample_months = sorted(list(set(sample_months)))  # Unique, sorted
        
        projection = project_investment_growth(
            current_value=float(goal.current_amount),
            monthly_contribution=0.0,
            months=months_remaining,
            annual_return=expected_return,
        )
        
        projection_samples = [
            {
                'month': month,
                'projected_balance': projection[min(month, len(projection) - 1)],
            }
            for month in sample_months
        ]
        
        achievable = metrics['achievable_with_planned_contribution']
        if achievable:
            achievable_count += 1
        
        total_progress += metrics['progress_percentage']
        
        goals_detail.append({
            'goal_id': str(goal.id),
            'goal_name': goal.goal_name,
            'goal_type': goal.goal_type,
            'status': goal.status,
            'priority': goal.priority,
            'target_amount': metrics['target_amount'],
            'current_amount': metrics['current_amount'],
            'remaining_amount': metrics['remaining_amount'],
            'progress_percentage': metrics['progress_percentage'],
            'target_date': goal.target_date.isoformat() if goal.target_date else None,
            'months_remaining': months_remaining,
            'required_monthly_sip': metrics['required_monthly_sip'],
            'projected_final_balance': metrics['projected_final_balance'],
            'achievable_with_planned_contribution': achievable,
            'projection_samples': projection_samples,
        })
    
    avg_progress = total_progress / len(goals) if goals else 0.0
    
    return {
        'count': len(goals),
        'goals': goals_detail,
        'achievement_summary': {
            'achievable_count': achievable_count,
            'total_goals': len(goals),
            'total_progress_percentage': _round_ratio(avg_progress, places=2),
        }
    }
