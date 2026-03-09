"""Portfolio Allocation Engine - generates recommended investment allocation.

Provides portfolio allocation recommendations based on:
- Risk tolerance (low, medium, high)
- Age / investment horizon
- Financial profile and constraints

Uses modern portfolio theory principles and ladder strategy for diversification.
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal


# Asset allocation rules by risk profile
RISK_PROFILES = {
    'low': {
        'equity': 40,
        'debt': 50,
        'gold': 10,
        'description': 'Conservative - Focus on capital preservation and steady income',
    },
    'medium': {
        'equity': 70,
        'debt': 20,
        'gold': 10,
        'description': 'Balanced - Growth with moderate income and safety',
    },
    'high': {
        'equity': 85,
        'debt': 10,
        'gold': 5,
        'description': 'Aggressive - Maximum growth potential with higher volatility',
    },
}

# Recommended instruments by asset class
INSTRUMENT_RECOMMENDATIONS = {
    'equity': {
        'long_term': [  # 10+ year horizon
            {
                'name': 'NIFTYBEES ETF',
                'description': 'Nifty 50 Index ETF',
                'type': 'index_etf',
                'risk_level': 'medium-high',
                'expense_ratio': 0.05,  # percentage
                'allocation_weight': 40,  # % of equity allocation
            },
            {
                'name': 'Midcap Index ETF',
                'description': 'Nifty Midcap 150 Index',
                'type': 'index_etf',
                'risk_level': 'high',
                'expense_ratio': 0.08,
                'allocation_weight': 30,
            },
            {
                'name': 'Sensex ETF (BSE)',
                'description': 'BSE Sensex tracking ETF',
                'type': 'index_etf',
                'risk_level': 'medium',
                'expense_ratio': 0.05,
                'allocation_weight': 30,
            },
        ],
        'medium_term': [  # 5-10 year horizon
            {
                'name': 'Balanced Mutual Fund',
                'description': 'Equity-Debt Mix Fund',
                'type': 'mutual_fund',
                'risk_level': 'medium',
                'expense_ratio': 0.75,
                'allocation_weight': 50,
            },
            {
                'name': 'NIFTYBEES ETF',
                'description': 'Nifty 50 Index ETF',
                'type': 'index_etf',
                'risk_level': 'medium-high',
                'expense_ratio': 0.05,
                'allocation_weight': 50,
            },
        ],
        'short_term': [  # 1-5 year horizon
            {
                'name': 'Large-Cap Mutual Fund',
                'description': 'Focused on stable, large companies',
                'type': 'mutual_fund',
                'risk_level': 'low-medium',
                'expense_ratio': 0.60,
                'allocation_weight': 100,
            },
        ],
    },
    'debt': {
        'government_securities': [
            {
                'name': 'Government Bond Fund',
                'description': 'Direct Government Securities',
                'type': 'bond_fund',
                'risk_level': 'very_low',
                'expense_ratio': 0.10,
                'allocation_weight': 50,
            },
        ],
        'corporate_bonds': [
            {
                'name': 'Corporate Bond Fund',
                'description': 'High-quality corporate bonds',
                'type': 'bond_fund',
                'risk_level': 'low',
                'expense_ratio': 0.30,
                'allocation_weight': 30,
            },
        ],
        'liquid_funds': [
            {
                'name': 'Liquid Mutual Fund',
                'description': 'Highly liquid short-term debt',
                'type': 'liquid_fund',
                'risk_level': 'very_low',
                'expense_ratio': 0.20,
                'allocation_weight': 20,
            },
        ],
    },
    'gold': {
        'etf': [
            {
                'name': 'Gold ETF',
                'description': 'Direct gold exposure via ETF',
                'type': 'commodity_etf',
                'risk_level': 'low',
                'expense_ratio': 0.40,
                'allocation_weight': 70,
            },
        ],
        'gold_fund': [
            {
                'name': 'Gold Mutual Fund',
                'description': 'Managed gold fund',
                'type': 'mutual_fund',
                'risk_level': 'low',
                'expense_ratio': 1.0,
                'allocation_weight': 30,
            },
        ],
    },
}


# ============================================================================
# MAIN RECOMMENDATION FUNCTION
# ============================================================================

def generate_portfolio_recommendation(
    risk_tolerance: str,
    age: Optional[int] = None,
    investment_horizon: Optional[int] = None,
    monthly_investment: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate portfolio allocation recommendation.
    
    Recommends asset allocation based on risk tolerance and investment horizon.
    Returns both allocation percentages and specific instrument recommendations
    with implementation strategy.
    
    Args:
        risk_tolerance: 'low', 'medium', or 'high'
        age: User age in years (optional, used to adjust recommendations)
        investment_horizon: Years until funds needed (optional, overrides age-based)
        monthly_investment: Planned monthly investment amount (optional)
        
    Returns:
        dict with keys:
            - recommended_portfolio: {equity, debt, gold} percentages
            - asset_class_instruments: Recommended instruments for each asset class
            - allocation_strategy: How to achieve the allocation
            - implementation_steps: Actionable steps to implement
            - rebalancing_strategy: When/how to rebalance
            - expected_characteristics: Risk-return profile
            - risk_profile_details: Description of risk profile
            - timestamp: Generation timestamp
            
    Raises:
        ValueError: If risk_tolerance invalid or parameters invalid
        
    Examples:
        >>> rec = generate_portfolio_recommendation('medium', age=35)
        >>> rec['recommended_portfolio']
        {'equity': 70, 'debt': 20, 'gold': 10}
        
        >>> rec = generate_portfolio_recommendation('high', investment_horizon=20)
        >>> rec['asset_class_instruments']['equity']
        [{'name': 'NIFTYBEES ETF', ...}, ...]
    """
    # Validate risk tolerance
    if risk_tolerance not in RISK_PROFILES:
        raise ValueError(
            f"Invalid risk_tolerance: {risk_tolerance}. "
            f"Must be one of: {list(RISK_PROFILES.keys())}"
        )
    
    # Validate numeric parameters
    if age is not None and (age < 18 or age > 120):
        raise ValueError(f"Age must be between 18 and 120, got {age}")
    
    if investment_horizon is not None and investment_horizon <= 0:
        raise ValueError(f"Investment horizon must be positive, got {investment_horizon}")
    
    if monthly_investment is not None and monthly_investment <= 0:
        raise ValueError(f"Monthly investment must be positive, got {monthly_investment}")
    
    # Determine investment horizon if not provided
    if investment_horizon is None and age is not None:
        # Default retirement age 60
        investment_horizon = max(60 - age, 1)
    
    # Get base allocation for risk tolerance (only numeric values)
    profile_data = RISK_PROFILES[risk_tolerance]
    allocation = {
        'equity': profile_data['equity'],
        'debt': profile_data['debt'],
        'gold': profile_data['gold'],
    }
    
    # Adjust allocation based on age/horizon if provided
    if investment_horizon is not None:
        allocation = _adjust_allocation_for_horizon(
            allocation, investment_horizon
        )
    
    # Generate instruments based on horizon
    horizon_category = _categorize_horizon(investment_horizon)
    instruments = _get_instruments_for_category(horizon_category)
    
    # Build strategy and implementation
    strategy = _build_allocation_strategy(
        allocation, instruments, monthly_investment
    )
    
    rebalancing = _get_rebalancing_strategy(investment_horizon)
    
    characteristics = _get_expected_characteristics(risk_tolerance)
    
    return {
        'recommended_portfolio': {
            'equity': _round_allocation(allocation['equity']),
            'debt': _round_allocation(allocation['debt']),
            'gold': _round_allocation(allocation['gold']),
        },
        'asset_class_instruments': instruments,
        'allocation_strategy': strategy,
        'implementation_steps': _generate_implementation_steps(
            allocation, monthly_investment
        ),
        'rebalancing_strategy': rebalancing,
        'expected_characteristics': characteristics,
        'risk_profile_details': RISK_PROFILES[risk_tolerance]['description'],
        'investment_horizon_years': investment_horizon,
        'timestamp': datetime.utcnow().isoformat(),
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _adjust_allocation_for_horizon(
    allocation: Dict[str, float],
    investment_horizon: int,
) -> Dict[str, float]:
    """Adjust allocation based on investment horizon.
    
    Rules:
    - Longer horizon (10+ years): Increase equity, decrease debt
    - Medium horizon (5-10 years): Keep balanced
    - Short horizon (<5 years): Increase debt and gold, decrease equity
    """
    adjusted = allocation.copy()
    
    if investment_horizon < 5:
        # Short term - priority on safety
        if adjusted['equity'] > 40:
            reduction = adjusted['equity'] - 40
            adjusted['equity'] = 40
            adjusted['debt'] += reduction * 0.8
            adjusted['gold'] += reduction * 0.2
    elif investment_horizon > 10:
        # Long term - priority on growth
        if adjusted['equity'] < 80:
            increase = min(80 - adjusted['equity'], 10)
            adjusted['equity'] += increase
            adjusted['debt'] -= increase * 0.7
            adjusted['gold'] -= increase * 0.3
    
    # Ensure allocations sum to 100
    total = sum(adjusted.values())
    if total != 100:
        scale_factor = 100 / total
        for key in adjusted:
            adjusted[key] *= scale_factor
    
    return adjusted


def _categorize_horizon(horizon: Optional[int]) -> str:
    """Categorize investment horizon into short/medium/long term."""
    if horizon is None:
        return 'medium_term'
    elif horizon < 5:
        return 'short_term'
    elif horizon < 10:
        return 'medium_term'
    else:
        return 'long_term'


def _get_instruments_for_category(category: str) -> Dict[str, List[Dict[str, Any]]]:
    """Get recommended instruments based on time horizon."""
    return {
        'equity': INSTRUMENT_RECOMMENDATIONS['equity'].get(
            category,
            INSTRUMENT_RECOMMENDATIONS['equity']['medium_term']
        ),
        'debt': _get_debt_instruments_for_category(category),
        'gold': INSTRUMENT_RECOMMENDATIONS['gold']['etf'] + 
                INSTRUMENT_RECOMMENDATIONS['gold']['gold_fund'],
    }


def _get_debt_instruments_for_category(category: str) -> List[Dict[str, Any]]:
    """Get debt instruments based on time horizon."""
    debt_rec = INSTRUMENT_RECOMMENDATIONS['debt']
    
    if category == 'short_term':
        # Shorter term: more liquid
        return (
            debt_rec['liquid_funds'] +
            debt_rec['government_securities']
        )
    elif category == 'long_term':
        # Longer term: can take more credit risk
        return (
            debt_rec['government_securities'] +
            debt_rec['corporate_bonds']
        )
    else:
        # Medium term: balanced
        return (
            debt_rec['government_securities'] +
            debt_rec['liquid_funds'] +
            debt_rec['corporate_bonds']
        )


def _build_allocation_strategy(
    allocation: Dict[str, float],
    instruments: Dict[str, List[Dict[str, Any]]],
    monthly_investment: Optional[float] = None,
) -> str:
    """Build detailed strategy description."""
    strategy = f"""
Asset Allocation Strategy:
- Equity: {allocation['equity']:.0f}% - Growth component
- Debt: {allocation['debt']:.0f}% - Income and stability
- Gold: {allocation['gold']:.0f}% - Inflation hedge and safety

Recommended Implementation:
1. Start with direct equity and debt instrument selection
2. Use index ETFs for low cost and diversification
3. Ensure proper fund house selection for consistent performance
4. Include both direct stocks and mutual funds for diversification

Risk-Adjusted Approach:
- Diversify across sectors and fund houses
- Balance growth and income components
- Maintain emergency fund in liquid assets
- Review and rebalance annually or when allocation drifts >5%
"""
    
    if monthly_investment:
        strategy += f"\nMonthly Investment Plan:\n"
        strategy += f"- Total Monthly: ₹{monthly_investment:,.2f}\n"
        strategy += f"- Equity allocation: ₹{(monthly_investment * allocation['equity'] / 100):,.2f}\n"
        strategy += f"- Debt allocation: ₹{(monthly_investment * allocation['debt'] / 100):,.2f}\n"
        strategy += f"- Gold allocation: ₹{(monthly_investment * allocation['gold'] / 100):,.2f}\n"
    
    return strategy.strip()


def _get_rebalancing_strategy(horizon: Optional[int]) -> Dict[str, Any]:
    """Get rebalancing strategy based on horizon."""
    if horizon is None or horizon > 10:
        frequency = "Annually"
        trigger = "Drift of 5%+ from target allocation"
    elif horizon > 5:
        frequency = "Semi-annually (2x per year)"
        trigger = "Drift of 3%+ from target allocation"
    else:
        frequency = "Quarterly (4x per year)"
        trigger = "Drift of 2%+ from target allocation"
    
    return {
        'frequency': frequency,
        'trigger_threshold': trigger,
        'method': 'Rebalance by redirecting new investments or repositioning existing',
        'tax_consideration': 'Review capital gains before rebalancing',
        'advisor_review': 'Annual review with financial advisor recommended',
    }


def _get_expected_characteristics(risk_tolerance: str) -> Dict[str, Any]:
    """Get expected return and risk characteristics."""
    characteristics = {
        'low': {
            'expected_annual_return': '5-6%',
            'expected_volatility': 'Low (5-8%)',
            'best_for': 'Conservative investors, near retirement, capital preservation',
            'max_drawdown_likely': '10-15%',
            'recovery_time': '1-2 years',
        },
        'medium': {
            'expected_annual_return': '8-10%',
            'expected_volatility': 'Medium (10-15%)',
            'best_for': 'Balanced investors, 10+ year horizon, moderate risk appetite',
            'max_drawdown_likely': '20-30%',
            'recovery_time': '3-5 years',
        },
        'high': {
            'expected_annual_return': '12-15%',
            'expected_volatility': 'High (15-25%)',
            'best_for': 'Aggressive investors, 15+ year horizon, high risk tolerance',
            'max_drawdown_likely': '40-50%',
            'recovery_time': '5-7 years',
        },
    }
    
    return characteristics.get(risk_tolerance, characteristics['medium'])


def _generate_implementation_steps(
    allocation: Dict[str, float],
    monthly_investment: Optional[float] = None,
) -> List[Dict[str, str]]:
    """Generate actionable implementation steps."""
    steps = [
        {
            'step': 1,
            'action': 'Assess current portfolio',
            'description': 'Document existing holdings and identify gaps',
        },
        {
            'step': 2,
            'action': 'Open required accounts',
            'description': 'Demat account for direct stocks, mutual fund accounts',
        },
        {
            'step': 3,
            'action': 'Start equity investments',
            'description': f"Allocate ₹{monthly_investment * allocation['equity'] / 100:,.2f} monthly to equity"
                          if monthly_investment else "Start with equity allocation",
        },
        {
            'step': 4,
            'action': 'Set up debt allocation',
            'description': f"Allocate ₹{monthly_investment * allocation['debt'] / 100:,.2f} monthly to debt"
                          if monthly_investment else "Start with debt allocation",
        },
        {
            'step': 5,
            'action': 'Allocate to gold',
            'description': f"Allocate ₹{monthly_investment * allocation['gold'] / 100:,.2f} monthly to gold"
                          if monthly_investment else "Build gold position",
        },
        {
            'step': 6,
            'action': 'Set up automatic investing',
            'description': 'Use SIP for regular and disciplined investing',
        },
        {
            'step': 7,
            'action': 'Monitor performance',
            'description': 'Review quarterly, rebalance annually',
        },
    ]
    
    return steps


def _round_allocation(value: float) -> float:
    """Round allocation percentage to 1 decimal place."""
    return round(value, 1)


def calculate_portfolio_value_at_horizon(
    initial_investment: float,
    monthly_sip: float,
    allocation: Dict[str, float],
    investment_horizon: int,
) -> Dict[str, Any]:
    """Project portfolio value at investment horizon.
    
    Uses expected returns for each asset class to project future value.
    
    Args:
        initial_investment: Starting amount (₹)
        monthly_sip: Monthly investment (₹)
        allocation: Dict with equity, debt, gold percentages
        investment_horizon: Years to project
        
    Returns:
        dict with projected values and details
        
    Example:
        >>> result = calculate_portfolio_value_at_horizon(100000, 10000, 
        ...                                                {'equity': 70, 'debt': 20, 'gold': 10}, 
        ...                                                10)
        >>> result['projected_final_value']
        4500000  # Approx ₹45 lakhs after 10 years
    """
    if investment_horizon <= 0:
        raise ValueError("Investment horizon must be positive")
    
    # Expected annual returns by asset class
    expected_returns = {
        'equity': 0.12,    # 12% annual
        'debt': 0.04,      # 4% annual
        'gold': 0.06,      # 6% annual inflation hedge
    }
    
    # Calculate weighted average return
    weighted_return = (
        (allocation.get('equity', 0) / 100) * expected_returns['equity'] +
        (allocation.get('debt', 0) / 100) * expected_returns['debt'] +
        (allocation.get('gold', 0) / 100) * expected_returns['gold']
    )
    
    # Project initial investment
    final_value = initial_investment * (1 + weighted_return) ** investment_horizon
    
    # Project SIP contributions (future value of annuity)
    # FV = PMT * [((1 + r)^n - 1) / r]
    months = investment_horizon * 12
    monthly_return = (1 + weighted_return) ** (1/12) - 1
    
    if monthly_return > 0:
        fv_sip = monthly_sip * (
            ((1 + monthly_return) ** months - 1) / monthly_return
        )
    else:
        fv_sip = monthly_sip * months
    
    total_invested = initial_investment + (monthly_sip * months)
    projected_total = final_value + fv_sip
    projected_gains = projected_total - total_invested
    
    return {
        'initial_investment': _round_currency(initial_investment),
        'monthly_sip': _round_currency(monthly_sip),
        'total_sip_invested': _round_currency(monthly_sip * months),
        'total_invested': _round_currency(total_invested),
        'projected_value_initial': _round_currency(final_value),
        'projected_value_sip': _round_currency(fv_sip),
        'projected_final_value': _round_currency(projected_total),
        'projected_gains': _round_currency(projected_gains),
        'weighted_annual_return': _round_ratio(weighted_return),
        'investment_horizon_years': investment_horizon,
        'cagr': _round_ratio(weighted_return),
    }


def get_risk_adjusted_recommendation(
    user_profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate risk-adjusted portfolio based on complete user profile.
    
    Considers:
    - Risk tolerance (explicit)
    - Financial capacity (income/expenses)
    - Emergency fund status
    - Age
    - Investment horizon
    
    Args:
        user_profile: Dict with keys:
            - risk_tolerance: 'low', 'medium', 'high'
            - age: int
            - monthly_income: float
            - monthly_expenses: float
            - emergency_fund_months: float
            - net_worth: float
            
    Returns:
        Enhanced recommendation with suitability assessment
    """
    risk_tolerance = user_profile.get('risk_tolerance', 'medium')
    age = user_profile.get('age')
    monthly_income = user_profile.get('monthly_income', 0)
    monthly_expenses = user_profile.get('monthly_expenses', 0)
    emergency_fund = user_profile.get('emergency_fund_months', 3)
    net_worth = user_profile.get('net_worth', 0)
    
    # Calculate investment capacity
    surplus = monthly_income - monthly_expenses
    
    # Generate base recommendation
    recommendation = generate_portfolio_recommendation(
        risk_tolerance=risk_tolerance,
        age=age,
        monthly_investment=max(surplus, 0),
    )
    
    # Add suitability assessment
    suitability = _assess_portfolio_suitability(
        risk_tolerance, age, monthly_income, monthly_expenses, 
        emergency_fund, net_worth
    )
    
    recommendation['suitability_assessment'] = suitability
    
    return recommendation


def _assess_portfolio_suitability(
    risk_tolerance: str,
    age: Optional[int],
    monthly_income: float,
    monthly_expenses: float,
    emergency_fund_months: float,
    net_worth: float,
) -> Dict[str, Any]:
    """Assess if portfolio is suitable for user profile."""
    concerns = []
    recommendations = []
    suitable = True
    
    # Check emergency fund
    if emergency_fund_months < 6:
        concerns.append(
            f"Emergency fund ({emergency_fund_months:.1f} months) below recommended 6 months"
        )
        recommendations.append(
            "Build emergency fund before aggressive investing"
        )
        suitable = False
    
    # Check income stability for high-risk profile
    if risk_tolerance == 'high' and monthly_income < 50000:
        concerns.append("Income may be limited for high-risk aggressive strategy")
        recommendations.append("Consider medium-risk profile with education and income growth plan")
    
    # Check debt levels
    debt_ratio = monthly_expenses / monthly_income if monthly_income > 0 else 1
    if debt_ratio > 0.8:
        concerns.append("High expense ratio limits investment capacity")
        recommendations.append("Reduce expenses or increase income before investing")
        suitable = False
    
    # Age and risk alignment
    if age and age < 25 and risk_tolerance == 'low':
        recommendations.append("Younger age allows higher risk tolerance; consider medium profile")
    
    if age and age > 60 and risk_tolerance == 'high':
        concerns.append("Age suggests conservative profile; high risk may not be appropriate")
        recommendations.append("Shift towards medium or conservative allocation")
    
    return {
        'suitable': suitable,
        'risk_tolerance': risk_tolerance,
        'concerns': concerns,
        'recommendations': recommendations,
        'key_metrics': {
            'monthly_income': _round_currency(monthly_income),
            'monthly_expenses': _round_currency(monthly_expenses),
            'monthly_surplus': _round_currency(max(monthly_income - monthly_expenses, 0)),
            'emergency_fund_months': _round_ratio(emergency_fund_months),
            'expense_to_income_ratio': _round_ratio(debt_ratio),
        },
    }


def _round_currency(value: float) -> float:
    """Round to 2 decimal places for currency."""
    return round(value, 2)


def _round_ratio(value: float) -> float:
    """Round to 4 decimal places for ratios/percentages."""
    return round(value, 4)
