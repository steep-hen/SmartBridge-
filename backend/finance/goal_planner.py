"""Goal Planning Engine - Calculate savings strategies for financial goals.

Uses SIP (Systematic Investment Plan) formula to calculate required monthly
investment and determine goal feasibility based on income and expenses.

SIP Formula: FV = P * ((1+r)^n - 1)/r
Solved for P: P = FV / (((1+r)^n - 1)/r)
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime
import math


def calculate_required_monthly_savings(
    target_amount: float,
    current_savings: float = 0,
    years: int = 5,
    expected_return: float = 0.08
) -> Dict[str, Any]:
    """Calculate required monthly SIP investment to reach target amount.
    
    Uses SIP (Systematic Investment Plan) formula to determine monthly
    contribution required to achieve a financial goal.
    
    Args:
        target_amount: Target financial goal in rupees
        current_savings: Current amount already saved (reduces target)
        years: Years available to reach goal (must be > 0)
        expected_return: Annual return rate as decimal (e.g., 0.08 for 8%)
    
    Returns:
        Dict with:
            - available: bool - Whether calculation succeeded
            - target_amount: float - Original target
            - current_savings: float - Current savings considered
            - net_target: float - Target after deducting current savings
            - years: int - Investment horizon
            - expected_annual_return: float - Expected annual return (%)
            - monthly_sip_required: float - Required monthly investment
            - total_investment: float - Sum of all monthly contributions
            - projected_returns: float - Expected capital gains
            - estimated_final_amount: float - Expected total value at target year
            - error: Optional[str] - Error message if calculation failed
    
    Raises:
        Handles edge cases gracefully with 'available': False
    
    Algorithm:
        1. Calculate net target (target - current savings)
        2. If net target <= 0, no investment needed
        3. Convert annual return to monthly: r = (1+annual_return)^(1/12) - 1
        4. Calculate number of months: n = years * 12
        5. Apply SIP formula: P = FV / (((1+r)^n - 1)/r)
        6. Calculate projected final amount for validation
    
    Example:
        >>> result = calculate_required_monthly_savings(
        ...     target_amount=500000,
        ...     current_savings=50000,
        ...     years=10,
        ...     expected_return=0.10
        ... )
        >>> print(f"Monthly SIP: ₹{result['monthly_sip_required']:,.0f}")
        >>> print(f"Feasibility: {result['monthly_sip_required']} per month")
    """
    try:
        # Validate inputs
        if target_amount <= 0 or years <= 0 or expected_return < 0:
            return {
                'available': False,
                'error': 'Invalid inputs: target and years must be > 0, return >= 0'
            }
        
        if expected_return > 1.0:  # Likely percentage instead of decimal
            expected_return = expected_return / 100
        
        # Calculate net target (reduce by current savings)
        net_target = max(0, target_amount - current_savings)
        
        # If target is already met
        if net_target <= 0:
            return {
                'available': True,
                'target_amount': target_amount,
                'current_savings': current_savings,
                'net_target': 0,
                'years': years,
                'expected_annual_return': expected_return * 100,
                'monthly_sip_required': 0,
                'total_investment': 0,
                'projected_returns': 0,
                'estimated_final_amount': _round_currency(current_savings),
                'message': 'Target already achieved with current savings'
            }
        
        # Convert annual return to monthly
        # Monthly rate = (1 + annual_rate)^(1/12) - 1
        monthly_rate = (1 + expected_return) ** (1/12) - 1
        
        # Number of months
        num_months = years * 12
        
        # SIP Formula: P = FV / (((1+r)^n - 1)/r)
        # Where:
        # P = monthly payment (what we're solving for)
        # FV = future value (target amount we want)
        # r = monthly rate
        # n = number of months
        
        if monthly_rate == 0:
            # If no return, simple division
            monthly_sip = net_target / num_months
        else:
            # Calculate using SIP formula
            numerator = net_target * monthly_rate
            denominator = ((1 + monthly_rate) ** num_months) - 1
            monthly_sip = numerator / denominator
        
        # Calculate total investment and projected final amount
        total_investment = monthly_sip * num_months
        
        # Projected final amount = current savings + SIP final value
        if monthly_rate == 0:
            sip_final_value = total_investment
        else:
            sip_final_value = monthly_sip * (((1 + monthly_rate) ** num_months - 1) / monthly_rate)
        
        estimated_final = current_savings + sip_final_value
        projected_returns = sip_final_value - total_investment
        
        return {
            'available': True,
            'target_amount': _round_currency(target_amount),
            'current_savings': _round_currency(current_savings),
            'net_target': _round_currency(net_target),
            'years': years,
            'expected_annual_return': _round_ratio(expected_return * 100),
            'monthly_sip_required': _round_currency(monthly_sip),
            'total_investment': _round_currency(total_investment),
            'projected_returns': _round_currency(projected_returns),
            'estimated_final_amount': _round_currency(estimated_final),
        }
    
    except (ZeroDivisionError, ValueError, OverflowError) as e:
        return {
            'available': False,
            'error': f'Calculation error: {str(e)}'
        }


def calculate_goal_feasibility(
    monthly_income: float,
    monthly_expenses: float,
    required_savings: float
) -> Dict[str, Any]:
    """Determine feasibility of achieving goal based on monthly budget.
    
    Evaluates whether required monthly savings is realistic based on
    available income (income - expenses).
    
    Args:
        monthly_income: Monthly gross income in rupees
        monthly_expenses: Total monthly expenses in rupees
        required_savings: Required monthly savings for goal (from calculate_required_monthly_savings)
    
    Returns:
        Dict with:
            - available: bool - Whether calculation succeeded
            - monthly_income: float - Monthly income
            - monthly_expenses: float - Monthly expenses
            - available_surplus: float - Income - Expenses
            - required_savings: float - Required for goal
            - savings_as_percent_of_income: float - % of income needed
            - feasibility_level: str - 'easy', 'moderate', 'difficult', 'unrealistic'
            - feasibility_color: str - 'green', 'yellow', 'orange', 'red'
            - shortfall: float - Amount not available (if negative surplus)
            - action_required: bool - Whether user action is needed
            - recommendations: List[str] - Suggestions to improve feasibility
    
    Feasibility Levels:
        - easy: Required savings < 20% of income (readily achievable)
        - moderate: 20-35% of income (requires moderate discipline)
        - difficult: 35-50% of income (requires significant lifestyle changes)
        - unrealistic: >= 50% of income (needs goal/timeline adjustment)
    
    Algorithm:
        1. Calculate available surplus = income - expenses
        2. Calculate savings percentage = required_savings / income
        3. Compare with thresholds to determine feasibility
        4. Generate recommendations based on feasibility level
    
    Example:
        >>> feasibility = calculate_goal_feasibility(
        ...     monthly_income=100000,
        ...     monthly_expenses=60000,
        ...     required_savings=8000
        ... )
        >>> print(f"Feasibility: {feasibility['feasibility_level']}")  # 'easy'
        >>> print(f"Surplus: ₹{feasibility['available_surplus']:,.0f}")
    """
    try:
        # Validate inputs
        if monthly_income <= 0 or monthly_expenses < 0 or required_savings < 0:
            return {
                'available': False,
                'error': 'Monthly income must be > 0; expenses and savings >= 0'
            }
        
        # Calculate available surplus
        available_surplus = monthly_income - monthly_expenses
        
        # Calculate savings as percentage of income
        if monthly_income > 0:
            savings_percent = (required_savings / monthly_income) * 100
        else:
            savings_percent = 0
        
        # Determine feasibility level
        if savings_percent < 20:
            level = 'easy'
            color = 'green'
        elif savings_percent < 35:
            level = 'moderate'
            color = 'yellow'
        elif savings_percent < 50:
            level = 'difficult'
            color = 'orange'
        else:
            level = 'unrealistic'
            color = 'red'
        
        # Check if action is required
        action_required = required_savings > available_surplus if available_surplus > 0 else True
        
        # Calculate shortfall (negative means deficit, positive means surplus)
        shortfall = available_surplus - required_savings
        
        # Generate recommendations
        recommendations = _generate_feasibility_recommendations(
            level, available_surplus, required_savings, monthly_income, monthly_expenses
        )
        
        return {
            'available': True,
            'monthly_income': _round_currency(monthly_income),
            'monthly_expenses': _round_currency(monthly_expenses),
            'available_surplus': _round_currency(available_surplus),
            'required_savings': _round_currency(required_savings),
            'savings_as_percent_of_income': _round_ratio(savings_percent),
            'feasibility_level': level,
            'feasibility_color': color,
            'shortfall': _round_currency(shortfall),  # Positive = can save more, Negative = deficit
            'action_required': action_required,
            'recommendations': recommendations,
        }
    
    except (ZeroDivisionError, ValueError) as e:
        return {
            'available': False,
            'error': f'Feasibility calculation error: {str(e)}'
        }


def generate_goal_strategy(
    goal_name: str,
    target_amount: float,
    current_savings: float,
    years: int,
    monthly_income: float,
    monthly_expenses: float,
    expected_return: float = 0.08
) -> Dict[str, Any]:
    """Generate comprehensive goal strategy combining SIP and feasibility analysis.
    
    Comprehensive function that calculates required SIP, evaluates feasibility,
    and provides actionable strategy recommendations.
    
    Args:
        goal_name: Name of the financial goal (e.g., "Buy House", "Education Fund")
        target_amount: Target amount for goal
        current_savings: Current amount already saved
        years: Years to achieve goal
        monthly_income: Monthly gross income
        monthly_expenses: Monthly total expenses
        expected_return: Expected annual return (default 8%)
    
    Returns:
        Dict with:
            - available: bool - Whether strategy generation succeeded
            - goal: str - Goal name
            - target_amount: float - Target amount
            - current_savings: float - Current savings
            - years_to_achieve: int - Timeline
            - required_monthly_sip: float - Monthly investment required
            - goal_feasibility: str - 'easy', 'moderate', 'difficult', 'unrealistic'
            - feasibility_color: str - Visual indicator
            - monthly_income: float - User's income
            - monthly_expenses: float - User's expenses
            - surplus_monthly: float - Available monthly surplus
            - strategy: List[str] - Actionable recommendations
            - action_items: List[Dict] - Detailed action items with impact
            - priority: str - 'HIGH', 'MEDIUM', 'LOW' based on effort needed
    
    Algorithm:
        1. Calculate required monthly SIP
        2. Assess feasibility
        3. Generate specific action items
        4. Prioritize recommendations by impact and ease
    
    Example:
        >>> strategy = generate_goal_strategy(
        ...     goal_name='Buy House',
        ...     target_amount=5000000,
        ...     current_savings=500000,
        ...     years=10,
        ...     monthly_income=150000,
        ...     monthly_expenses=90000,
        ...     expected_return=0.08
        ... )
        >>> print(f"Strategy for {strategy['goal']}")
        >>> for rec in strategy['strategy']:
        ...     print(f"  • {rec}")
    """
    try:
        # Get SIP calculation
        sip_result = calculate_required_monthly_savings(
            target_amount, current_savings, years, expected_return
        )
        
        if not sip_result.get('available'):
            return {'available': False, 'error': sip_result.get('error')}
        
        # Get feasibility assessment
        feasibility_result = calculate_goal_feasibility(
            monthly_income,
            monthly_expenses,
            sip_result['monthly_sip_required']
        )
        
        if not feasibility_result.get('available'):
            return {'available': False, 'error': feasibility_result.get('error')}
        
        # Determine priority
        savings_percent = feasibility_result['savings_as_percent_of_income']
        if savings_percent < 15:
            priority = 'LOW'
        elif savings_percent < 35:
            priority = 'MEDIUM'
        else:
            priority = 'HIGH'
        
        # Combine strategies from feasibility recommendations
        base_strategy = feasibility_result['recommendations']
        
        # Add goal-specific strategies
        additional_strategy = _generate_goal_specific_strategies(
            goal_name,
            target_amount,
            sip_result['monthly_sip_required'],
            feasibility_result['feasibility_level'],
            monthly_income,
            years
        )
        
        combined_strategy = base_strategy + additional_strategy
        
        # Create action items with estimated impact
        action_items = _create_action_items(
            combined_strategy,
            monthly_income,
            monthly_expenses,
            sip_result['monthly_sip_required']
        )
        
        return {
            'available': True,
            'goal': goal_name,
            'target_amount': sip_result['target_amount'],
            'current_savings': sip_result['current_savings'],
            'net_target': sip_result['net_target'],
            'years_to_achieve': years,
            'required_monthly_sip': sip_result['monthly_sip_required'],
            'total_investment_required': sip_result['total_investment'],
            'projected_gains': sip_result['projected_returns'],
            'expected_annual_return': sip_result['expected_annual_return'],
            'goal_feasibility': feasibility_result['feasibility_level'],
            'feasibility_color': feasibility_result['feasibility_color'],
            'monthly_income': feasibility_result['monthly_income'],
            'monthly_expenses': feasibility_result['monthly_expenses'],
            'surplus_monthly': feasibility_result['available_surplus'],
            'savings_as_percent': feasibility_result['savings_as_percent_of_income'],
            'strategy': combined_strategy,
            'action_items': action_items,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
        }
    
    except Exception as e:
        return {
            'available': False,
            'error': f'Strategy generation failed: {str(e)}'
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_feasibility_recommendations(
    level: str,
    available_surplus: float,
    required_savings: float,
    monthly_income: float,
    monthly_expenses: float
) -> List[str]:
    """Generate recommendations based on feasibility level.
    
    Args:
        level: Feasibility level ('easy', 'moderate', 'difficult', 'unrealistic')
        available_surplus: Monthly income - expenses
        required_savings: Required monthly savings
        monthly_income: Monthly income
        monthly_expenses: Monthly expenses
    
    Returns:
        List of actionable recommendations
    """
    recommendations = []
    
    if level == 'easy':
        recommendations.append(
            f"✓ Goal is achievable. You can comfortably save ₹{required_savings:,.0f}/month"
        )
        recommendations.append(
            "Consider automating monthly transfers to goal account"
        )
        recommendations.append(
            "Explore investment options (mutual funds, fixed deposits) for better returns"
        )
    
    elif level == 'moderate':
        # Calculate potential expense reduction
        expense_reduction = (required_savings - available_surplus) if available_surplus < required_savings else 0
        if expense_reduction > 0:
            recommendations.append(
                f"Reduce discretionary spending by ₹{expense_reduction:,.0f}/month to meet goal"
            )
        else:
            recommendations.append(
                f"Goal is achievable with current budget. Savings rate: {(required_savings/monthly_income)*100:.1f}%"
            )
        recommendations.append(
            "Review subscriptions and recurring expenses for optimization"
        )
        recommendations.append(
            "Consider side income to boost savings capacity"
        )
    
    elif level == 'difficult':
        # Calculate significant expense reduction needed
        gap = required_savings - available_surplus
        recommendations.append(
            f"Significant lifestyle changes needed. Reduce expenses by ₹{gap:,.0f}/month"
        )
        recommendations.append(
            "Prioritize goal and eliminate non-essential spending (subscriptions, dining out, etc.)"
        )
        recommendations.append(
            f"Even with disciplined spending, savings rate would be {(required_savings/monthly_income)*100:.1f}% of income"
        )
        recommendations.append(
            "Consider extending goal timeline to reduce monthly burden"
        )
        recommendations.append(
            "Explore ways to increase income (career growth, side business)"
        )
    
    else:  # unrealistic
        recommendations.append(
            f"Current goal is unrealistic. Required savings: {(required_savings/monthly_income)*100:.1f}% of income"
        )
        recommendations.append(
            "RECOMMENDED: Extend timeline to 15-20 years to reduce monthly investment"
        )
        recommendations.append(
            "OR: Reduce target amount to make goal achievable"
        )
        recommendations.append(
            "OR: Focus on increasing income significantly"
        )
        recommendations.append(
            "Consider breaking goal into smaller milestones"
        )
    
    return recommendations


def _generate_goal_specific_strategies(
    goal_name: str,
    target_amount: float,
    monthly_sip: float,
    feasibility: str,
    monthly_income: float,
    years: int
) -> List[str]:
    """Generate goal-specific strategies and recommendations.
    
    Args:
        goal_name: Name of goal
        target_amount: Target amount
        monthly_sip: Required monthly SIP
        feasibility: Feasibility level
        monthly_income: Monthly income
        years: Years to achieve
    
    Returns:
        List of goal-specific recommendations
    """
    strategies = []
    
    # Investment strategy recommendations
    if years >= 10:
        strategies.append(
            "Invest in equity mutual funds (60-70% allocation) for better long-term returns"
        )
    elif years >= 5:
        strategies.append(
            "Balanced portfolio: 50% equity, 50% fixed income for moderate growth with stability"
        )
    else:
        strategies.append(
            "Conservative approach: Debt mutual funds or fixed deposits for capital preservation"
        )
    
    # Savings rate optimization
    savings_percent = (monthly_sip / monthly_income) * 100
    if savings_percent < 10:
        strategies.append(
            f"Savings rate of {savings_percent:.1f}% is healthy. Maintain and potentially increase as income grows"
        )
    else:
        strategies.append(
            f"Aggressive savings rate ({savings_percent:.1f}%). Ensure goal aligns with life priorities"
        )
    
    # Goal-specific tips
    goal_lower = goal_name.lower()
    if 'house' in goal_lower or 'property' in goal_lower or 'home' in goal_lower:
        strategies.append(
            "Research home loan options to reduce upfront savings needed"
        )
        strategies.append(
            "Factor in property appreciation when setting investment strategy"
        )
    
    elif 'education' in goal_lower or 'school' in goal_lower or 'college' in goal_lower:
        strategies.append(
            "Education costs inflate at 5-7% annually. Account for this in your plan"
        )
        strategies.append(
            "Explore education-focused schemes and scholarships"
        )
    
    elif 'retirement' in goal_lower or 'pension' in goal_lower:
        strategies.append(
            "Maximize tax-advantaged accounts (PPF, NPS, ELSS) for better post-tax returns"
        )
        strategies.append(
            "Create diversified portfolio across asset classes"
        )
    
    elif 'wedding' in goal_lower or 'marriage' in goal_lower:
        strategies.append(
            "Most of the funds will be needed in short-term. Shift to safer investments 2 years before"
        )
        strategies.append(
            "Budget inflation at 3-5% annually for wedding expenses"
        )
    
    elif 'car' in goal_lower or 'vehicle' in goal_lower or 'bike' in goal_lower:
        strategies.append(
            "Consider vehicle financing options to reduce upfront investment burden"
        )
        strategies.append(
            "Factor in insurance, registration, and maintenance costs"
        )
    
    else:
        strategies.append(
            "Diversify investments across asset classes based on risk tolerance"
        )
        strategies.append(
            "Review and rebalance portfolio annually"
        )
    
    return strategies


def _create_action_items(
    strategies: List[str],
    monthly_income: float,
    monthly_expenses: float,
    required_savings: float
) -> List[Dict[str, Any]]:
    """Convert strategy recommendations into actionable items with impact estimates.
    
    Args:
        strategies: List of strategy recommendations
        monthly_income: Monthly income
        monthly_expenses: Monthly expenses
        required_savings: Required monthly savings
    
    Returns:
        List of action items with impact and priority
    """
    action_items = []
    
    # Categorize and add impacts
    for i, strategy in enumerate(strategies, 1):
        strategy_lower = strategy.lower()
        
        # Determine action type and impact
        if 'reduce' in strategy_lower or 'discretionary' in strategy_lower:
            # Extract amount if mentioned
            amount = 0
            words = strategy.split()
            for j, word in enumerate(words):
                if word == '₹' and j + 1 < len(words):
                    try:
                        amount = float(words[j + 1].replace(',', ''))
                    except:
                        pass
            
            action_items.append({
                'id': i,
                'action': strategy,
                'category': 'expense_reduction',
                'estimated_impact': _round_currency(amount) if amount > 0 else 'Variable',
                'priority': 'HIGH',
                'difficulty': 'MEDIUM',
                'timeline': '1 month'
            })
        
        elif 'automate' in strategy_lower or 'invest' in strategy_lower:
            action_items.append({
                'id': i,
                'action': strategy,
                'category': 'investment',
                'estimated_impact': 'Enhanced returns',
                'priority': 'HIGH',
                'difficulty': 'LOW',
                'timeline': 'Immediate'
            })
        
        elif 'income' in strategy_lower or 'side' in strategy_lower:
            action_items.append({
                'id': i,
                'action': strategy,
                'category': 'income_generation',
                'estimated_impact': 'Custom',
                'priority': 'MEDIUM',
                'difficulty': 'HIGH',
                'timeline': '3-6 months'
            })
        
        elif 'extend' in strategy_lower or 'timeline' in strategy_lower:
            action_items.append({
                'id': i,
                'action': strategy,
                'category': 'timeline_adjustment',
                'estimated_impact': 'Reduces monthly burden',
                'priority': 'MEDIUM',
                'difficulty': 'LOW',
                'timeline': 'Planning phase'
            })
        
        else:
            action_items.append({
                'id': i,
                'action': strategy,
                'category': 'general',
                'estimated_impact': 'Varies',
                'priority': 'MEDIUM',
                'difficulty': 'MEDIUM',
                'timeline': 'Ongoing'
            })
    
    return action_items


def _round_currency(value: float) -> float:
    """Round currency values to 2 decimal places.
    
    Args:
        value: Value to round
    
    Returns:
        Rounded value
    """
    return round(float(value), 2)


def _round_ratio(value: float) -> float:
    """Round ratio/percentage values to 2 decimal places.
    
    Args:
        value: Value to round
    
    Returns:
        Rounded value
    """
    return round(float(value), 2)
