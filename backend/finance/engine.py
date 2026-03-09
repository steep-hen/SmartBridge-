"""Pure-function financial analysis engine.

Deterministic calculations for personal financial metrics.
All functions are stateless and return consistent results given same inputs.

Mathematical Conventions:
- All monetary values are in base currency units (e.g., USD dollars)
- All interest rates are annual (e.g., 0.07 = 7% APR)
- All time periods are in months unless otherwise specified
- Rounding: 2 decimal places for currency, 4 for ratios/percentages
- Compounding: Monthly (applied at month-end)

Formula References:
- SIP FV: FV = PMT × [((1 + r)^n - 1) / r]  where r = annual_rate / 12
- Investment Growth: discretized monthly compounding with monthly contributions
"""

from typing import Optional, List, Dict, Tuple
import numpy as np
from decimal import Decimal, ROUND_HALF_UP


# ============================================================================
# ROUNDING & PRECISION UTILITIES
# ============================================================================

def _round_currency(value: float) -> float:
    """Round monetary value to 2 decimal places (nearest cent).
    
    Uses banker's rounding (ROUND_HALF_UP) for consistent behavior.
    
    Args:
        value: Monetary amount
        
    Returns:
        float: Rounded to 2 decimal places
    """
    if not isinstance(value, (int, float)):
        return value
    d = Decimal(str(float(value)))
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _round_ratio(value: float, places: int = 4) -> float:
    """Round ratio/percentage to specified decimal places.
    
    Args:
        value: Ratio or percentage
        places: Number of decimal places (default: 4)
        
    Returns:
        float: Rounded value
    """
    if not isinstance(value, (int, float)):
        return value
    quantizer = Decimal(10) ** -places
    d = Decimal(str(float(value)))
    return float(d.quantize(quantizer, rounding=ROUND_HALF_UP))


# ============================================================================
# BASIC METRICS
# ============================================================================

def compute_savings_rate(
    monthly_income: float,
    monthly_savings: float,
) -> float:
    """Calculate savings rate as percentage of income.
    
    Formula: savings_rate = (monthly_savings / monthly_income) × 100
    
    Savings rate = portion of income that is saved (not spent).
    Useful benchmark: 20% is considered healthy by most financial advisors.
    
    Args:
        monthly_income: Gross monthly income (positive)
        monthly_savings: Monthly amount saved (non-negative)
        
    Returns:
        float: Savings rate as percentage (0-100+)
        
    Edge Cases:
        - Zero income returns 0.0 (person is not saving percentage-wise)
        - Negative income returns 0.0
        - monthly_savings > monthly_income returns >100% (undersaver scenario)
    """
    if monthly_income <= 0:
        return 0.0
    
    rate = (monthly_savings / monthly_income) * 100.0
    return _round_ratio(rate, places=2)


def compute_debt_to_income_ratio(
    total_debt: float,
    monthly_income: float,
) -> float:
    """Calculate debt-to-income (DTI) ratio.
    
    Formula: DTI = total_debt / (monthly_income × 12)
    
    DTI measures total debt as multiple of annual income.
    Ratios < 0.3 (30%) are generally considered healthy.
    Ratios > 0.5 (50%) indicate high leverage.
    
    Args:
        total_debt: Total outstanding debt (non-negative)
        monthly_income: Gross monthly income (positive)
        
    Returns:
        float: Debt-to-income ratio (e.g., 0.25 = 25%)
        
    Edge Cases:
        - Zero income returns 0.0
        - Negative income returns 0.0
        - Zero debt returns 0.0
    """
    if monthly_income <= 0:
        return 0.0
    
    annual_income = monthly_income * 12
    ratio = total_debt / annual_income
    return _round_ratio(ratio, places=4)


def compute_emergency_fund_months(
    savings_balance: float,
    monthly_expenses: float,
) -> float:
    """Calculate emergency fund coverage in months.
    
    Formula: emergency_months = savings_balance / monthly_expenses
    
    Measures how many months of expenses current savings covers.
    Target: 3-6 months is typical (varies by risk tolerance, job security).
    
    Args:
        savings_balance: Liquid savings available (non-negative)
        monthly_expenses: Average monthly expenses (positive)
        
    Returns:
        float: Months of coverage (e.g., 3.5 = 3.5 months)
        
    Edge Cases:
        - Zero expenses returns 0.0 (edge case: person has no expenses)
        - Negative expenses returns 0.0
        - Savings > expenses = high coverage ( > 1 month per month of expense)
    """
    if monthly_expenses <= 0:
        return 0.0
    
    months = savings_balance / monthly_expenses
    return _round_ratio(months, places=2)


# ============================================================================
# INVESTMENT CALCULATIONS
# ============================================================================

def compute_required_sip(
    target_amount: float,
    current_value: float,
    months: int,
    expected_annual_return: float,
) -> float:
    """Calculate Systematic Investment Plan (SIP) monthly contribution needed.
    
    Formula (Annuity Future Value):
        FV = PV × (1 + r)^n + PMT × [((1 + r)^n - 1) / r]
        
        Where:
        - FV = target_amount
        - PV = current_value
        - r = expected_annual_return / 12
        - n = months
        - PMT = monthly contribution (solving for this)
    
    Rearranged:
        PMT = (target_amount - PV × (1 + r)^n) / [((1 + r)^n - 1) / r]
    
    Compounding: Monthly (applies at month-end after contribution).
    
    Args:
        target_amount: Desired future value (positive)
        current_value: Current investment balance (non-negative)
        months: Investment horizon (positive int)
        expected_annual_return: Annual rate of return (e.g., 0.07 = 7%)
        
    Returns:
        float: Required monthly contribution (non-negative)
        
    Notes:
        - Negative result indicates current_value exceeds target
        - Returns 0.0 if current_value >= target_amount and monthly_return > 0
        - If expected_annual_return == 0 (no growth), uses simple formula: (target - current) / months
        
    Example:
        >>> compute_required_sip(target_amount=100000, current_value=10000, months=120, expected_annual_return=0.07)
        # Returns monthly SIP needed to reach $100k in 10 years starting from $10k with 7% annual return
    """
    if months <= 0:
        return 0.0
    
    target = max(0.0, target_amount)
    current = max(0.0, current_value)
    
    # If already at or above target, no contribution needed
    if current >= target:
        return 0.0
    
    # Monthly rate
    r_monthly = expected_annual_return / 12
    
    # Handle special case: zero return (no interest)
    if abs(r_monthly) < 1e-10:
        remaining = target - current
        monthly_sip = remaining / max(1, months)
        return _round_currency(max(0.0, monthly_sip))
    
    # Future value of current balance
    fv_current = current * ((1 + r_monthly) ** months)
    
    # Remaining amount to achieve
    remaining_fv = target - fv_current
    
    # If remaining is non-positive, already on track
    if remaining_fv <= 0:
        return 0.0
    
    # Annuity factor for FV calculation
    annuity_factor = (((1 + r_monthly) ** months) - 1) / r_monthly
    
    # Monthly contribution needed
    monthly_sip = remaining_fv / annuity_factor
    
    return _round_currency(max(0.0, monthly_sip))


def project_investment_growth(
    current_value: float,
    monthly_contribution: float,
    months: int,
    annual_return: float,
) -> List[float]:
    """Project investment growth with monthly compounding and contributions.
    
    Formula (discrete compounding at month-end):
        balance[i] = balance[i-1] × (1 + r_monthly) + monthly_contribution
        
        Where:
        - r_monthly = annual_return / 12
        - i = month index
    
    Timeline:
        - Month 0: Starting balance (before any contribution/interest)
        - Month 1: Starting balance grows, then we add contribution
        - Each month: Previous balance × (1 + rate) + contribution
    
    Contributions: Added at end of month (after interest accrual).
    
    Args:
        current_value: Starting balance (non-negative)
        monthly_contribution: Contribution per month (non-negative)
        months: Projection horizon (positive int)
        annual_return: Expected annual return (e.g., 0.07 = 7%)
        
    Returns:
        List[float]: Monthly projected balances, length = months + 1
                     [month_0_balance, month_1_balance, ..., month_n_balance]
        
    Notes:
        - Array includes initial balance at index 0
        - Each subsequent value is end-of-month balance after interest and contribution
        - Deterministic: Same inputs always produce same output
        - Uses numpy for efficiency on large projections
        
    Example:
        >>> project_investment_growth(10000, 500, 120, 0.07)
        # Returns array with 121 values showing monthly progression
    """
    if months <= 0:
        return [_round_currency(current_value)]
    
    current = max(0.0, current_value)
    contrib = max(0.0, monthly_contribution)
    r_monthly = annual_return / 12
    
    # Initialize array with starting balance
    balances = np.zeros(months + 1, dtype=np.float64)
    balances[0] = current
    
    # Simulate month-by-month
    for i in range(1, months + 1):
        new_balance = balances[i - 1] * (1 + r_monthly) + contrib
        balances[i] = new_balance
    
    # Round to 2 decimal places for currency
    return [_round_currency(float(b)) for b in balances]


# ============================================================================
# SCORING & COMPOSITE METRICS
# ============================================================================

def compute_financial_health_score(metrics: Dict[str, float]) -> int:
    """Compute composite financial health score (0-100).
    
    Weighted scoring based on multiple financial indicators.
    
    Scoring Components (weights):
        1. savings_rate (25%): Target > 20% optimal
           - 0% savings → 0 points
           - 20% savings → 50 points
           - 30%+ savings → 100 points
           
        2. emergency_fund_months (25%): Target 3-6 months
           - < 1 month → 0 points
           - 3 months → 100 points
           - 6+ months → 100 points (capped)
           
        3. debt_to_income_ratio (25%): Target < 30%
           - > 50% DTI → 0 points
           - 30% DTI → 100 points
           - < 10% DTI → 100 points (excellent)
           
        4. investment_ratio (25%): % of net worth in investments
           - 0% investments → 0 points
           - 25%+ investments → 100 points
    
    Calculation:
        health_score = Σ(component_score × weight)
        Clamped to [0, 100]
    
    Args:
        metrics: Dict containing optional keys:
            - savings_rate: float (0-100+), percentage
            - emergency_fund_months: float (≥0), months of expenses
            - debt_to_income_ratio: float (0-1+), ratio
            - investment_ratio: float (0-1), proportion of net worth
            - other keys: ignored
            
    Returns:
        int: Health score 0-100
        
    Notes:
        - Empty dict (no data) returns 0 (no financeial information)
        - Missing keys default to 0 (worst case for that component)
        - Gracefully handles zero/negative inputs
        - Final score is integer (rounded)
    """
    # If no metrics provided, user has no data - return 0
    if not metrics:
        return 0
    
    score_components = {}
    
    # 1. Savings Rate Component (25%)
    savings_rate = max(0.0, metrics.get('savings_rate', 0.0))
    if savings_rate == 0:
        savings_component = 0.0
    elif savings_rate >= 30:
        savings_component = 100.0
    else:
        # Linear scaling: 0% -> 0, 20% -> 50, 30% -> 100
        savings_component = min(100.0, (savings_rate / 30.0) * 100.0)
    score_components['savings_rate'] = savings_component * 0.25
    
    # 2. Emergency Fund Component (25%)
    emergency_months = max(0.0, metrics.get('emergency_fund_months', 0.0))
    if emergency_months == 0:
        emergency_component = 0.0
    elif emergency_months >= 3:
        emergency_component = 100.0
    else:
        # Linear scaling: 0 -> 0, 3 -> 100
        emergency_component = (emergency_months / 3.0) * 100.0
    score_components['emergency_fund'] = emergency_component * 0.25
    
    # 3. Debt-to-Income Component (25%)
    dti_ratio = max(0.0, metrics.get('debt_to_income_ratio', 0.0))
    if dti_ratio >= 0.50:
        dti_component = 0.0
    elif dti_ratio <= 0.10:
        dti_component = 100.0
    else:
        # Inverse scaling: 50% -> 0, 30% -> 100, 10% -> 100
        # Map [0.10, 0.50] to [100, 0]
        dti_component = max(0.0, (0.50 - dti_ratio) / 0.40 * 100.0)
    score_components['debt_to_income'] = dti_component * 0.25
    
    # 4. Investment Ratio Component (25%)
    investment_ratio = max(0.0, min(1.0, metrics.get('investment_ratio', 0.0)))
    if investment_ratio == 0:
        investment_component = 0.0
    elif investment_ratio >= 0.25:
        investment_component = 100.0
    else:
        # Linear scaling: 0 -> 0, 25% -> 100
        investment_component = (investment_ratio / 0.25) * 100.0
    score_components['investment_ratio'] = investment_component * 0.25
    
    # Aggregate
    total_score = sum(score_components.values())
    
    return int(round(min(100.0, max(0.0, total_score))))


# ============================================================================
# BATCH UTILITIES
# ============================================================================

def compute_goal_metrics(
    goal_target: float,
    goal_current: float,
    goal_monthly_increment: float,
    months_remaining: int,
    expected_annual_return: float,
) -> Dict[str, float]:
    """Compute metrics for a single financial goal.
    
    Combines current progress, required monthly contribution, and projection.
    
    Args:
        goal_target: Target amount
        goal_current: Current balance towards goal
        goal_monthly_increment: Planned monthly addition to goal
        months_remaining: Months until target date
        expected_annual_return: Annual return expectation
        
    Returns:
        dict with keys:
            - target_amount
            - current_amount
            - remaining_amount
            - progress_percentage
            - required_monthly_sip
            - projected_final_balance
            - achievable_with_planned_contribution (bool)
    """
    remaining = max(0.0, goal_target - goal_current)
    progress_pct = (goal_current / goal_target * 100) if goal_target > 0 else 0.0
    
    required_sip = compute_required_sip(
        goal_target, goal_current, months_remaining, expected_annual_return
    )
    
    # Project with current monthly increment
    projection = project_investment_growth(
        goal_current, goal_monthly_increment, months_remaining, expected_annual_return
    )
    projected_final = projection[-1] if projection else goal_current
    
    achievable = projected_final >= goal_target
    
    return {
        'target_amount': _round_currency(goal_target),
        'current_amount': _round_currency(goal_current),
        'remaining_amount': _round_currency(remaining),
        'progress_percentage': _round_ratio(progress_pct, places=2),
        'required_monthly_sip': _round_currency(required_sip),
        'projected_final_balance': _round_currency(projected_final),
        'achievable_with_planned_contribution': achievable,
    }
