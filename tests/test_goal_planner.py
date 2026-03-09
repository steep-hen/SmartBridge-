"""Unit tests for goal planning engine.

Tests SIP calculations, goal feasibility assessment, and strategy generation.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from backend.finance.goal_planner import (
    calculate_required_monthly_savings,
    calculate_goal_feasibility,
    generate_goal_strategy,
)


# ============================================================================
# TESTS: Required Monthly Savings (SIP Calculation)
# ============================================================================

def test_calculate_required_monthly_savings_basic():
    """Test basic SIP calculation with standard inputs."""
    result = calculate_required_monthly_savings(
        target_amount=500000,
        current_savings=0,
        years=10,
        expected_return=0.08
    )
    
    assert result['available'] == True
    assert result['target_amount'] == 500000
    assert result['monthly_sip_required'] > 0
    assert result['years'] == 10


def test_calculate_required_monthly_savings_with_current_savings():
    """Test SIP calculation when user already has some savings."""
    result = calculate_required_monthly_savings(
        target_amount=500000,
        current_savings=100000,
        years=5,
        expected_return=0.08
    )
    
    assert result['available'] == True
    # Net target should be reduced by current savings
    assert result['net_target'] == 400000
    # Monthly SIP should be less than without current savings
    assert result['monthly_sip_required'] > 0


def test_calculate_required_monthly_savings_target_met():
    """Test when current savings exceed target."""
    result = calculate_required_monthly_savings(
        target_amount=100000,
        current_savings=150000,
        years=5,
        expected_return=0.08
    )
    
    assert result['available'] == True
    assert result['monthly_sip_required'] == 0
    assert result['message'] == 'Target already achieved with current savings'


def test_calculate_required_monthly_savings_zero_return():
    """Test SIP with zero expected return (simple savings)."""
    result = calculate_required_monthly_savings(
        target_amount=600000,
        current_savings=0,
        years=10,
        expected_return=0.0
    )
    
    assert result['available'] == True
    # With 0% return, monthly = 600000 / (10*12) = 5000
    assert abs(result['monthly_sip_required'] - 5000.0) < 1.0


def test_calculate_required_monthly_savings_high_return():
    """Test SIP with high expected return reduces monthly requirement."""
    result_low = calculate_required_monthly_savings(
        target_amount=500000,
        years=10,
        expected_return=0.05
    )
    
    result_high = calculate_required_monthly_savings(
        target_amount=500000,
        years=10,
        expected_return=0.10
    )
    
    # Higher return should require lower monthly SIP
    assert result_high['monthly_sip_required'] < result_low['monthly_sip_required']


def test_calculate_required_monthly_savings_invalid_inputs():
    """Test error handling for invalid inputs."""
    # Negative target
    result = calculate_required_monthly_savings(
        target_amount=-100000,
        years=5,
        expected_return=0.08
    )
    assert result['available'] == False
    
    # Zero years
    result = calculate_required_monthly_savings(
        target_amount=500000,
        years=0,
        expected_return=0.08
    )
    assert result['available'] == False


def test_calculate_required_monthly_savings_percentage_as_decimal():
    """Test percentage input as decimal vs percentage."""
    result = calculate_required_monthly_savings(
        target_amount=500000,
        years=10,
        expected_return=8  # Passed as 8 instead of 0.08
    )
    
    # Should still work - function converts percentage to decimal
    assert result['available'] == True


def test_calculate_required_monthly_savings_final_amount():
    """Test projected final amount matches target."""
    result = calculate_required_monthly_savings(
        target_amount=500000,
        current_savings=0,
        years=10,
        expected_return=0.08
    )
    
    assert result['available'] == True
    # Projected final should approximately equal target
    assert abs(result['estimated_final_amount'] - 500000) < 500  # Within 500 rupees


# ============================================================================
# TESTS: Goal Feasibility
# ============================================================================

def test_calculate_goal_feasibility_easy():
    """Test easy feasibility level."""
    result = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=60000,
        required_savings=10000  # 10% of income
    )
    
    assert result['available'] == True
    assert result['feasibility_level'] == 'easy'
    assert result['feasibility_color'] == 'green'
    assert result['action_required'] == False


def test_calculate_goal_feasibility_moderate():
    """Test moderate feasibility level."""
    result = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=60000,
        required_savings=25000  # 25% of income
    )
    
    assert result['available'] == True
    assert result['feasibility_level'] == 'moderate'
    assert result['feasibility_color'] == 'yellow'


def test_calculate_goal_feasibility_difficult():
    """Test difficult feasibility level."""
    result = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=60000,
        required_savings=40000  # 40% of income
    )
    
    assert result['available'] == True
    assert result['feasibility_level'] == 'difficult'
    assert result['feasibility_color'] == 'orange'


def test_calculate_goal_feasibility_unrealistic():
    """Test unrealistic feasibility level."""
    result = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=60000,
        required_savings=60000  # 60% of income
    )
    
    assert result['available'] == True
    assert result['feasibility_level'] == 'unrealistic'
    assert result['feasibility_color'] == 'red'


def test_calculate_goal_feasibility_deficit():
    """Test when required savings exceed available surplus."""
    result = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=90000,
        required_savings=15000  # More than surplus of 10000
    )
    
    assert result['available'] == True
    assert result['action_required'] == True
    # Shortfall should be negative
    assert result['shortfall'] < 0


def test_calculate_goal_feasibility_has_surplus():
    """Test when surplus allows for additional savings."""
    result = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=60000,
        required_savings=30000  # Less than surplus of 40000
    )
    
    assert result['available'] == True
    # Shortfall should be positive (surplus available)
    assert result['shortfall'] > 0


def test_calculate_goal_feasibility_recommendations():
    """Test that recommendations are generated for each level."""
    result_easy = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=60000,
        required_savings=8000
    )
    
    result_difficult = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=60000,
        required_savings=45000
    )
    
    # Both should have recommendations
    assert len(result_easy['recommendations']) > 0
    assert len(result_difficult['recommendations']) > 0
    
    # Different levels should have different recommendations
    assert result_easy['recommendations'] != result_difficult['recommendations']


# ============================================================================
# TESTS: Goal Strategy Generation
# ============================================================================

def test_generate_goal_strategy_basic():
    """Test basic goal strategy generation."""
    strategy = generate_goal_strategy(
        goal_name='Buy House',
        target_amount=5000000,
        current_savings=500000,
        years=10,
        monthly_income=150000,
        monthly_expenses=90000,
        expected_return=0.08
    )
    
    assert strategy['available'] == True
    assert strategy['goal'] == 'Buy House'
    assert strategy['target_amount'] == 5000000
    assert strategy['required_monthly_sip'] > 0
    assert strategy['goal_feasibility'] in ['easy', 'moderate', 'difficult', 'unrealistic']


def test_generate_goal_strategy_feasibility():
    """Test strategy includes feasibility assessment."""
    strategy = generate_goal_strategy(
        goal_name='Education Fund',
        target_amount=500000,
        current_savings=100000,
        years=15,
        monthly_income=80000,
        monthly_expenses=50000,
        expected_return=0.07
    )
    
    assert strategy['available'] == True
    assert 'goal_feasibility' in strategy
    assert 'feasibility_color' in strategy
    assert strategy['feasibility_color'] in ['green', 'yellow', 'orange', 'red']


def test_generate_goal_strategy_includes_action_items():
    """Test that strategy includes detailed action items."""
    strategy = generate_goal_strategy(
        goal_name='Retirement Fund',
        target_amount=10000000,
        current_savings=1000000,
        years=20,
        monthly_income=200000,
        monthly_expenses=100000,
        expected_return=0.09
    )
    
    assert strategy['available'] == True
    assert 'action_items' in strategy
    assert len(strategy['action_items']) > 0
    
    # Each action item should have required fields
    for item in strategy['action_items']:
        assert 'action' in item
        assert 'category' in item
        assert 'priority' in item


def test_generate_goal_strategy_house_goal():
    """Test goal-specific strategies for house purchase."""
    strategy = generate_goal_strategy(
        goal_name='Buy House',
        target_amount=5000000,
        current_savings=500000,
        years=10,
        monthly_income=150000,
        monthly_expenses=90000,
    )
    
    assert strategy['available'] == True
    # Should include house-specific recommendations
    assert any('home loan' in rec.lower() or 'property' in rec.lower() 
               for rec in strategy['strategy'])


def test_generate_goal_strategy_education_goal():
    """Test goal-specific strategies for education."""
    strategy = generate_goal_strategy(
        goal_name='Child Education Fund',
        target_amount=1500000,
        current_savings=200000,
        years=10,
        monthly_income=120000,
        monthly_expenses=70000,
    )
    
    assert strategy['available'] == True
    # Should include education-specific recommendations
    assert any('education' in rec.lower() or 'inflation' in rec.lower()
               for rec in strategy['strategy'])


def test_generate_goal_strategy_priority_assignment():
    """Test priority assignment based on difficulty."""
    strategy_easy = generate_goal_strategy(
        goal_name='Goal 1',
        target_amount=100000,
        years=10,
        monthly_income=200000,
        monthly_expenses=100000,
    )
    
    strategy_hard = generate_goal_strategy(
        goal_name='Goal 2',
        target_amount=500000,
        years=2,
        monthly_income=100000,
        monthly_expenses=80000,
    )
    
    assert strategy_easy['available'] == True
    assert strategy_hard['available'] == True
    
    # Easy goal should have lower priority
    assert strategy_easy['priority'] == 'LOW'
    # Hard goal should have higher priority
    assert strategy_hard['priority'] == 'HIGH'


def test_generate_goal_strategy_invalid_inputs():
    """Test error handling in strategy generation."""
    result = generate_goal_strategy(
        goal_name='',
        target_amount=-100000,
        years=-5,
        monthly_income=0,
        monthly_expenses=0,
    )
    
    assert result['available'] == False
    assert 'error' in result


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_goal_strategy_full_workflow():
    """Test complete workflow: SIP calculation -> Feasibility -> Strategy."""
    # Define goal
    goal_name = 'Vacation Trip'
    target = 500000
    current = 50000
    years = 3
    monthly_income = 100000
    monthly_expenses = 60000
    
    # Step 1: Calculate required SIP
    sip = calculate_required_monthly_savings(
        target_amount=target,
        current_savings=current,
        years=years,
        expected_return=0.08
    )
    
    assert sip['available'] == True
    monthly_needed = sip['monthly_sip_required']
    
    # Step 2: Check feasibility
    feasibility = calculate_goal_feasibility(
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        required_savings=monthly_needed
    )
    
    assert feasibility['available'] == True
    
    # Step 3: Generate full strategy
    strategy = generate_goal_strategy(
        goal_name=goal_name,
        target_amount=target,
        current_savings=current,
        years=years,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
    )
    
    assert strategy['available'] == True
    # All should be consistent
    assert strategy['required_monthly_sip'] == monthly_needed
    assert strategy['goal_feasibility'] == feasibility['feasibility_level']


def test_multiple_goals_different_timelines():
    """Test strategies for goals with different timelines."""
    goals = [
        {'name': 'Short-term', 'amount': 200000, 'years': 1},
        {'name': 'Medium-term', 'amount': 1000000, 'years': 5},
        {'name': 'Long-term', 'amount': 5000000, 'years': 20},
    ]
    
    monthly_income = 150000
    monthly_expenses = 90000
    
    strategies = []
    for goal in goals:
        strategy = generate_goal_strategy(
            goal_name=goal['name'],
            target_amount=goal['amount'],
            current_savings=0,
            years=goal['years'],
            monthly_income=monthly_income,
            monthly_expenses=monthly_expenses,
        )
        strategies.append(strategy)
    
    # All should be valid
    assert all(s['available'] for s in strategies)
    
    # Longer term goals should require lower monthly SIP
    sips = [s['required_monthly_sip'] for s in strategies]
    assert sips[0] > sips[1] > sips[2]  # Short > Medium > Long


def test_goal_strategy_updates_with_changed_income():
    """Test that strategy reflects changes in income."""
    # Low income scenario
    strategy_low = generate_goal_strategy(
        goal_name='House',
        target_amount=5000000,
        current_savings=500000,
        years=10,
        monthly_income=80000,
        monthly_expenses=60000,
    )
    
    # High income scenario
    strategy_high = generate_goal_strategy(
        goal_name='House',
        target_amount=5000000,
        current_savings=500000,
        years=10,
        monthly_income=200000,
        monthly_expenses=100000,
    )
    
    # With higher income, feasibility should improve
    assert strategy_low['available'] == True
    assert strategy_high['available'] == True
    
    # High income scenario should have better feasibility
    feasibility_map = {'easy': 1, 'moderate': 2, 'difficult': 3, 'unrealistic': 4}
    assert feasibility_map[strategy_high['goal_feasibility']] <= feasibility_map[strategy_low['goal_feasibility']]


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_sip_calculation_very_high_return():
    """Test SIP calculation with unrealistically high returns."""
    result = calculate_required_monthly_savings(
        target_amount=1000000,
        years=5,
        expected_return=0.50  # 50% annual return
    )
    
    assert result['available'] == True
    # Very high returns mean very low monthly requirement
    assert result['monthly_sip_required'] < 1000


def test_sip_calculation_very_long_timeline():
    """Test SIP with very long investment horizon."""
    result = calculate_required_monthly_savings(
        target_amount=10000000,
        years=50,
        expected_return=0.08
    )
    
    assert result['available'] == True
    # Long timeline should reduce monthly requirement
    assert result['monthly_sip_required'] > 0


def test_feasibility_extreme_expenses():
    """Test feasibility when expenses nearly equal income."""
    result = calculate_goal_feasibility(
        monthly_income=100000,
        monthly_expenses=99000,
        required_savings=5000
    )
    
    assert result['available'] == True
    # Should be unrealistic
    assert result['feasibility_level'] == 'unrealistic'


def test_strategy_zero_current_savings():
    """Test strategy with no current savings (starting from scratch)."""
    strategy = generate_goal_strategy(
        goal_name='Savings Goal',
        target_amount=100000,
        current_savings=0,
        years=1,
        monthly_income=50000,
        monthly_expenses=30000,
    )
    
    assert strategy['available'] == True
    assert strategy['current_savings'] == 0


def test_strategy_very_short_timeline():
    """Test strategy with very short timeline (aggressive savings)."""
    strategy = generate_goal_strategy(
        goal_name='Emergency',
        target_amount=200000,
        current_savings=0,
        years=1,
        monthly_income=100000,
        monthly_expenses=60000,
    )
    
    assert strategy['available'] == True
    # Very short timeline should require high monthly SIP
    assert strategy['required_monthly_sip'] > strategy['monthly_income'] * 0.15
