"""Goal Progress Tracking Engine - Calculate progress towards financial goals.

Tracks goal progress with:
- Current progress percentage
- Expected completion date based on monthly savings
- Time remaining to goal completion
- Visual data for dashboards and charts
- Feasibility analysis and projections

Uses financial calculations to estimate when goals will be achieved.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import math


# ============================================================================
# ROUNDING & PRECISION UTILITIES
# ============================================================================

def _round_currency(value: float) -> float:
    """Round monetary value to 2 decimal places.
    
    Args:
        value: Monetary amount
        
    Returns:
        float: Rounded to 2 decimal places
    """
    if not isinstance(value, (int, float)):
        return value
    d = Decimal(str(float(value)))
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _round_ratio(value: float, places: int = 2) -> float:
    """Round ratio/percentage to specified decimal places.
    
    Args:
        value: Ratio or percentage
        places: Number of decimal places (default: 2)
        
    Returns:
        float: Rounded value
    """
    if not isinstance(value, (int, float)):
        return value
    quantizer = Decimal(10) ** -places
    d = Decimal(str(float(value)))
    return float(d.quantize(quantizer, rounding=ROUND_HALF_UP))


# ============================================================================
# CORE PROGRESS CALCULATIONS
# ============================================================================

def calculate_goal_progress(
    target_amount: float,
    current_amount: float,
) -> Dict[str, float]:
    """Calculate progress percentage towards goal.
    
    Determines how close user is to achieving their financial goal
    based on current savings vs target amount.
    
    Args:
        target_amount: Target goal amount in rupees (required, > 0)
        current_amount: Current amount saved/accumulated (>= 0)
        
    Returns:
        Dict with:
            - goal_progress_percent: float (0-100)
            - remaining_amount: float
            - progress_status: str ("Not Started", "In Progress", "Nearly Complete", "Complete")
            
    Example:
        >>> progress = calculate_goal_progress(
        ...     target_amount=500000,
        ...     current_amount=250000
        ... )
        >>> print(progress['goal_progress_percent'])  # Output: 50.0
        >>> print(progress['progress_status'])        # Output: "In Progress"
    """
    
    # Validate inputs
    if target_amount <= 0:
        return {
            'goal_progress_percent': 0.0,
            'remaining_amount': 0.0,
            'progress_status': 'Invalid Target',
            'error': 'Target amount must be positive'
        }
    
    if current_amount < 0:
        current_amount = 0
    
    # Calculate progress percentage
    progress_percent = (current_amount / target_amount) * 100
    progress_percent = min(100, progress_percent)  # Cap at 100%
    progress_percent = max(0, progress_percent)    # Floor at 0%
    
    # Determine status
    if progress_percent >= 100:
        progress_status = "Complete"
    elif progress_percent >= 75:
        progress_status = "Nearly Complete"
    elif progress_percent >= 25:
        progress_status = "In Progress"
    elif progress_percent > 0:
        progress_status = "Just Started"
    else:
        progress_status = "Not Started"
    
    remaining_amount = max(0, target_amount - current_amount)
    
    return {
        'goal_progress_percent': _round_ratio(progress_percent, places=1),
        'remaining_amount': _round_currency(remaining_amount),
        'progress_status': progress_status,
    }


def calculate_time_remaining(
    target_amount: float,
    current_amount: float,
    monthly_contribution: float,
    target_date: Optional[date] = None,
    annual_return: float = 0.06,
) -> Dict[str, Any]:
    """Calculate time remaining to complete goal.
    
    Estimates months remaining until goal is achieved based on:
    - Remaining savings needed
    - Monthly contribution rate
    - Expected returns on investments
    - Target date (if specified)
    
    Args:
        target_amount: Target goal amount (> 0)
        current_amount: Current savings/amount (>= 0)
        monthly_contribution: Monthly contribution amount (>= 0)
        target_date: User's desired target date (optional)
        annual_return: Expected annual return on savings (default: 6%)
        
    Returns:
        Dict with:
            - months_remaining: int - Estimated months to goal completion
            - years_remaining: float - Years remaining (formatted)
            - expected_completion_date: str - "YYYY-MM" format
            - on_track: bool - Whether goal is achievable by target_date
            - time_until_target_date: Optional[int] - Months between now and target
            - feasible: bool - Achievable with current contribution
            - message: str - Status message
            
    Example:
        >>> time_left = calculate_time_remaining(
        ...     target_amount=500000,
        ...     current_amount=250000,
        ...     monthly_contribution=5000,
        ...     target_date=date(2026, 12, 31)
        ... )
        >>> print(time_left['expected_completion_date'])  # "2026-10"
        >>> print(time_left['on_track'])                   # True/False
    """
    
    # Validate inputs
    if target_amount <= 0:
        return {
            'months_remaining': 0,
            'years_remaining': 0.0,
            'expected_completion_date': None,
            'on_track': False,
            'feasible': False,
            'message': 'Invalid target amount',
            'error': 'Target amount must be positive'
        }
    
    if current_amount >= target_amount:
        today = datetime.utcnow().date()
        return {
            'months_remaining': 0,
            'years_remaining': 0.0,
            'expected_completion_date': today.strftime('%Y-%m'),
            'on_track': True,
            'feasible': True,
            'message': 'Goal already achieved!',
        }
    
    # Handle zero contribution (no progress possible)
    if monthly_contribution <= 0:
        return {
            'months_remaining': float('inf'),
            'years_remaining': float('inf'),
            'expected_completion_date': None,
            'on_track': False,
            'feasible': False,
            'message': 'No monthly contribution - goal unreachable',
        }
    
    # Calculate remaining amount needed
    remaining_amount = target_amount - current_amount
    
    # Calculate monthly return rate
    monthly_return = (1 + annual_return) ** (1/12) - 1
    
    # Solve for months using FV = PV * (1+r)^n + PMT * [((1+r)^n - 1) / r]
    # Where:
    # FV = target_amount
    # PV = current_amount
    # PMT = monthly_contribution
    # r = monthly_return
    
    # Iterative calculation (binary search for months)
    months = _calculate_months_for_target(
        target_amount=target_amount,
        current_amount=current_amount,
        monthly_contribution=monthly_contribution,
        monthly_return=monthly_return,
    )
    
    if months is None or months > 600:  # More than 50 years
        return {
            'months_remaining': 600,
            'years_remaining': 50.0,
            'expected_completion_date': None,
            'on_track': False,
            'feasible': False,
            'message': 'Goal will take too long with current contribution',
        }
    
    # Calculate expected completion date
    today = datetime.utcnow().date()
    completion_date = today + timedelta(days=months * 30)  # Approximate
    completion_date_str = completion_date.strftime('%Y-%m')
    
    years_remaining = months / 12
    
    # Check if on track with target date
    on_track = True
    time_until_target_date = None
    if target_date:
        time_until_target_date = _months_between_dates(today, target_date)
        on_track = months <= time_until_target_date
    
    return {
        'months_remaining': int(max(0, months)),
        'years_remaining': _round_ratio(years_remaining, places=1),
        'expected_completion_date': completion_date_str,
        'on_track': on_track,
        'time_until_target_date': time_until_target_date,
        'feasible': True,
        'message': 'On track' if on_track else 'Behind schedule - increase contribution',
    }


def _calculate_months_for_target(
    target_amount: float,
    current_amount: float,
    monthly_contribution: float,
    monthly_return: float,
    max_iterations: int = 100,
) -> Optional[int]:
    """Calculate months needed to reach target using binary search.
    
    Args:
        target_amount: Target final value
        current_amount: Current balance
        monthly_contribution: Monthly SIP amount
        monthly_return: Monthly return rate (decimal, e.g., 0.005)
        max_iterations: Max iterations for binary search
        
    Returns:
        Number of months needed, or None if unreachable
    """
    
    # Calculate future value given n months
    def future_value(months: float) -> float:
        if months <= 0:
            return current_amount
        
        m = max(0, months)  # Ensure non-negative
        
        # FV = PV * (1+r)^n + PMT * [((1+r)^n - 1) / r]
        try:
            compound_factor = (1 + monthly_return) ** m
            fv = current_amount * compound_factor
            
            if monthly_return > 0.0001:  # Avoid division by near-zero
                sip_factor = (compound_factor - 1) / monthly_return
                fv += monthly_contribution * sip_factor
            else:  # For near-zero return, use simple addition
                fv += monthly_contribution * m
            
            return fv
        except (OverflowError, ValueError):
            return float('inf')
    
    # Binary search for months
    low, high = 0, 600  # 50 years max
    
    for _ in range(max_iterations):
        mid = (low + high) / 2
        fv = future_value(mid)
        
        if abs(fv - target_amount) < 1:  # Within ₹1 accuracy
            return int(mid)
        elif fv < target_amount:
            low = mid
        else:
            high = mid
    
    # Return best estimate after iterations
    return int((low + high) / 2) if future_value((low + high) / 2) >= target_amount else None


def _months_between_dates(date1: date, date2: date) -> int:
    """Calculate months between two dates.
    
    Args:
        date1: Start date
        date2: End date
        
    Returns:
        Number of months between dates (positive if date2 > date1)
    """
    return (date2.year - date1.year) * 12 + (date2.month - date1.month)


# ============================================================================
# COMPREHENSIVE GOAL PROGRESS ANALYSIS
# ============================================================================

def get_goal_progress_analysis(
    goal_id: str,
    goal_name: str,
    target_amount: float,
    current_amount: float,
    target_date: Optional[date],
    monthly_contribution: float = 0.0,
    annual_return: float = 0.06,
    goal_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Get comprehensive progress analysis for a single goal.
    
    Combines progress percentage, time remaining, and projections
    into a single comprehensive analysis for dashboard display.
    
    Args:
        goal_id: Unique goal ID
        goal_name: Name of the goal
        target_amount: Target amount for the goal
        current_amount: Current savings/accumulation
        target_date: User's target completion date
        monthly_contribution: Monthly contribution towards goal
        annual_return: Expected annual return on savings
        goal_type: Type of goal (SAVINGS, INVESTMENT, EDUCATION, etc.)
        
    Returns:
        Dict with:
            - goal_id: Goal identifier
            - goal_name: Goal name
            - goal_type: Type of goal
            - goal_progress: {...} (from calculate_goal_progress)
            - time_remaining: {...} (from calculate_time_remaining)
            - progress_percent: Number for progress bar (0-100)
            - expected_completion_date: "YYYY-MM" format
            - monthly_required: Recommended monthly contribution if behind
            - priority_recommendation: String (Increase contribution / On track / Increase frequency)
            
    Example:
        >>> analysis = get_goal_progress_analysis(
        ...     goal_id="goal-123",
        ...     goal_name="Home Purchase",
        ...     target_amount=500000,
        ...     current_amount=200000,
        ...     target_date=date(2028, 12, 31),
        ...     monthly_contribution=5000
        ... )
        >>> print(f"Progress: {analysis['progress_percent']}%")
        >>> print(f"Completion: {analysis['expected_completion_date']}")
    """
    
    # Calculate progress
    progress = calculate_goal_progress(target_amount, current_amount)
    
    # Calculate time remaining
    time_remaining = calculate_time_remaining(
        target_amount=target_amount,
        current_amount=current_amount,
        monthly_contribution=monthly_contribution,
        target_date=target_date,
        annual_return=annual_return,
    )
    
    # Calculate recommended monthly contribution if behind
    monthly_required = _calculate_required_monthly_contribution(
        target_amount=target_amount,
        current_amount=current_amount,
        months_available=time_remaining.get('time_until_target_date', 12),
        annual_return=annual_return,
    )
    
    # Priority recommendation
    if progress['goal_progress_percent'] >= 100:
        priority = "Completed"
    elif not time_remaining.get('on_track', False):
        if monthly_contribution < monthly_required:
            priority = f"Increase contribution to ₹{monthly_required:,.0f}/month to stay on track"
        else:
            priority = "Increase investment frequency"
    elif progress['goal_progress_percent'] < 25:
        priority = "Prioritize this goal"
    else:
        priority = "On track"
    
    return {
        'goal_id': goal_id,
        'goal_name': goal_name,
        'goal_type': goal_type or 'SAVINGS',
        'goal_progress': progress,
        'time_remaining': time_remaining,
        'progress_percent': progress['goal_progress_percent'],
        'expected_completion_date': time_remaining.get('expected_completion_date'),
        'months_remaining': time_remaining.get('months_remaining', 0),
        'years_remaining': time_remaining.get('years_remaining', 0),
        'monthly_required': _round_currency(monthly_required),
        'current_monthly_contribution': _round_currency(monthly_contribution),
        'on_track': time_remaining.get('on_track', False),
        'priority_recommendation': priority,
        'target_amount': _round_currency(target_amount),
        'current_amount': _round_currency(current_amount),
        'remaining_amount': progress['remaining_amount'],
    }


def _calculate_required_monthly_contribution(
    target_amount: float,
    current_amount: float,
    months_available: int,
    annual_return: float = 0.06,
) -> float:
    """Calculate required monthly contribution to reach target.
    
    Args:
        target_amount: Target amount
        current_amount: Current savings
        months_available: Months until target date
        annual_return: Expected annual return
        
    Returns:
        Required monthly contribution in rupees
    """
    
    if months_available <= 0 or target_amount <= 0:
        return 0.0
    
    remaining = target_amount - current_amount
    
    if remaining <= 0:
        return 0.0
    
    # Calculate monthly return
    monthly_return = (1 + annual_return) ** (1/12) - 1
    
    # Use SIP formula: P = FV / (((1+r)^n - 1) / r)
    if monthly_return > 0.0001:
        factor = ((1 + monthly_return) ** months_available - 1) / monthly_return
    else:
        factor = months_available
    
    required_monthly = remaining / max(factor, 1)
    
    return _round_currency(max(0, required_monthly))


def calculate_goal_highlights(
    goals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Calculate key highlights across all goals.
    
    Args:
        goals: List of goal progress analysis dicts
        
    Returns:
        Dict with:
            - total_goals: Count of all goals
            - goals_completed: Count of completed goals
            - completion_rate: Percentage of completed goals
            - goals_on_track: Count of on-track goals
            - goals_behind: Count of behind-schedule goals
            - average_progress: Average progress % across all goals
            - highest_priority_goal: Goal with most progress needed
            - closest_completion: Goal closest to completion
    """
    
    if not goals:
        return {
            'total_goals': 0,
            'goals_completed': 0,
            'completion_rate': 0,
            'goals_on_track': 0,
            'goals_behind': 0,
            'average_progress': 0,
            'highest_priority_goal': None,
            'closest_completion': None,
        }
    
    total = len(goals)
    completed = sum(1 for g in goals if g['progress_percent'] >= 100)
    on_track = sum(1 for g in goals if g.get('on_track', False))
    behind = sum(1 for g in goals if not g.get('on_track', False) and g['progress_percent'] < 100)
    avg_progress = sum(g['progress_percent'] for g in goals) / total if total > 0 else 0
    
    # Find highest priority (least progress)
    highest_priority = min(
        (g for g in goals if g['progress_percent'] < 100),
        key=lambda g: g['progress_percent'],
        default=None
    )
    
    # Find closest to completion
    closest = max(
        (g for g in goals if g['progress_percent'] < 100),
        key=lambda g: g['progress_percent'],
        default=None
    )
    
    return {
        'total_goals': total,
        'goals_completed': completed,
        'completion_rate': _round_ratio((completed / total) * 100, places=1) if total > 0 else 0,
        'goals_on_track': on_track,
        'goals_behind': behind,
        'average_progress': _round_ratio(avg_progress, places=1),
        'highest_priority_goal': highest_priority,
        'closest_completion': closest,
    }
