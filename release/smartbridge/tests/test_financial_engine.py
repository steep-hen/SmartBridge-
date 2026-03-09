"""Unit tests for financial engine calculations.

Tests all pure functions in backend/finance/engine.py with focus on:
- Correctness of formulas
- Edge cases (zero, negative, very large values)
- Numerical stability and rounding consistency
"""

import pytest
from decimal import Decimal

from backend.finance.engine import (
    compute_savings_rate,
    compute_debt_to_income_ratio,
    compute_emergency_fund_months,
    compute_required_sip,
    project_investment_growth,
    compute_financial_health_score,
    compute_goal_metrics,
)


# ============================================================================
# SAVINGS RATE TESTS
# ============================================================================

class TestSavingsRate:
    """Test compute_savings_rate()"""
    
    def test_basic_calculation(self):
        """10% of $5000 = $500 saved."""
        rate = compute_savings_rate(monthly_income=5000.0, monthly_savings=500.0)
        assert rate == pytest.approx(10.0, abs=0.01)
    
    def test_high_savings_rate(self):
        """30% savings rate."""
        rate = compute_savings_rate(monthly_income=10000.0, monthly_savings=3000.0)
        assert rate == pytest.approx(30.0, abs=0.01)
    
    def test_zero_savings(self):
        """No savings -> 0% rate."""
        rate = compute_savings_rate(monthly_income=5000.0, monthly_savings=0.0)
        assert rate == 0.0
    
    def test_zero_income(self):
        """Zero income -> 0% (edge case)."""
        rate = compute_savings_rate(monthly_income=0.0, monthly_savings=1000.0)
        assert rate == 0.0
    
    def test_negative_income(self):
        """Negative income -> 0% (edge case)."""
        rate = compute_savings_rate(monthly_income=-5000.0, monthly_savings=500.0)
        assert rate == 0.0
    
    def test_oversaving(self):
        """Saving more than income -> >100%."""
        rate = compute_savings_rate(monthly_income=5000.0, monthly_savings=6000.0)
        assert rate > 100.0
    
    def test_rounding_to_2_decimals(self):
        """Result rounded to 2 decimal places."""
        rate = compute_savings_rate(monthly_income=3.0, monthly_savings=1.0)
        # 1/3 * 100 = 33.333... -> 33.33
        assert rate == pytest.approx(33.33, abs=0.01)


# ============================================================================
# DEBT-TO-INCOME TESTS
# ============================================================================

class TestDebtToIncome:
    """Test compute_debt_to_income_ratio()"""
    
    def test_basic_calculation(self):
        """$60k debt / $200k annual income = 0.30 (30%)."""
        dti = compute_debt_to_income_ratio(total_debt=60000.0, monthly_income=16666.67)
        assert dti == pytest.approx(0.30, abs=0.01)
    
    def test_zero_debt(self):
        """No debt -> 0.0 ratio."""
        dti = compute_debt_to_income_ratio(total_debt=0.0, monthly_income=5000.0)
        assert dti == 0.0
    
    def test_zero_income(self):
        """Zero income -> 0.0 (edge case)."""
        dti = compute_debt_to_income_ratio(total_debt=50000.0, monthly_income=0.0)
        assert dti == 0.0
    
    def test_negative_income(self):
        """Negative income -> 0.0 (edge case)."""
        dti = compute_debt_to_income_ratio(total_debt=50000.0, monthly_income=-5000.0)
        assert dti == 0.0
    
    def test_high_leverage(self):
        """Very high debt -> high ratio."""
        dti = compute_debt_to_income_ratio(total_debt=500000.0, monthly_income=1000.0)
        assert dti > 1.0  # Debt > annual income
    
    def test_rounding_to_4_decimals(self):
        """Result rounded to 4 decimal places."""
        dti = compute_debt_to_income_ratio(total_debt=16666.0, monthly_income=5000.0)
        # Should be some fractional value rounded to 4 places
        assert len(str(dti).split('.')[-1]) <= 4


# ============================================================================
# EMERGENCY FUND TESTS
# ============================================================================

class TestEmergencyFund:
    """Test compute_emergency_fund_months()"""
    
    def test_basic_calculation(self):
        """$9000 savings / $3000 monthly expenses = 3 months."""
        months = compute_emergency_fund_months(
            savings_balance=9000.0, monthly_expenses=3000.0
        )
        assert months == pytest.approx(3.0, abs=0.01)
    
    def test_partial_month(self):
        """$5000 / $3000 = 1.67 months."""
        months = compute_emergency_fund_months(
            savings_balance=5000.0, monthly_expenses=3000.0
        )
        assert months == pytest.approx(1.67, abs=0.01)
    
    def test_zero_expenses(self):
        """Zero expenses -> 0.0 (edge case)."""
        months = compute_emergency_fund_months(
            savings_balance=10000.0, monthly_expenses=0.0
        )
        assert months == 0.0
    
    def test_negative_expenses(self):
        """Negative expenses -> 0.0 (edge case)."""
        months = compute_emergency_fund_months(
            savings_balance=10000.0, monthly_expenses=-1000.0
        )
        assert months == 0.0
    
    def test_zero_savings(self):
        """No savings -> 0 months coverage."""
        months = compute_emergency_fund_months(
            savings_balance=0.0, monthly_expenses=3000.0
        )
        assert months == 0.0


# ============================================================================
# SIP CALCULATION TESTS
# ============================================================================

class TestRequiredSIP:
    """Test compute_required_sip() with standard FV formula"""
    
    def test_from_zero_no_return(self):
        """No starting amount, no returns -> simple division."""
        sip = compute_required_sip(
            target_amount=100000.0,
            current_value=0.0,
            months=120,  # 10 years
            expected_annual_return=0.0,
        )
        # $100,000 / 120 months = $833.33/month
        assert sip == pytest.approx(833.33, abs=1.0)
    
    def test_already_at_target(self):
        """Current value >= target -> no SIP needed."""
        sip = compute_required_sip(
            target_amount=50000.0,
            current_value=50000.0,
            months=120,
            expected_annual_return=0.07,
        )
        assert sip == 0.0
    
    def test_with_returns(self):
        """With compound growth, required SIP is lower."""
        sip_no_return = compute_required_sip(
            target_amount=100000.0,
            current_value=0.0,
            months=120,
            expected_annual_return=0.0,
        )
        
        sip_with_return = compute_required_sip(
            target_amount=100000.0,
            current_value=0.0,
            months=120,
            expected_annual_return=0.07,
        )
        
        # With returns, should need less monthly
        assert sip_with_return < sip_no_return
    
    def test_zero_months(self):
        """Zero time horizon -> 0 SIP."""
        sip = compute_required_sip(
            target_amount=100000.0,
            current_value=0.0,
            months=0,
            expected_annual_return=0.07,
        )
        assert sip == 0.0
    
    def test_negative_months(self):
        """Negative time -> 0 SIP."""
        sip = compute_required_sip(
            target_amount=100000.0,
            current_value=0.0,
            months=-12,
            expected_annual_return=0.07,
        )
        assert sip == 0.0


# ============================================================================
# INVESTMENT PROJECTION TESTS
# ============================================================================

class TestProjectionGrowth:
    """Test project_investment_growth() with discrete monthly compounding"""
    
    def test_no_contribution_no_return(self):
        """Starting balance constant with no returns/contributions."""
        projection = project_investment_growth(
            current_value=10000.0,
            monthly_contribution=0.0,
            months=12,
            annual_return=0.0,
        )
        
        assert len(projection) == 13  # 0 to 12 inclusive
        assert projection[0] == 10000.0
        assert projection[12] == 10000.0
    
    def test_contributions_no_return(self):
        """Linear growth with contributions but no return."""
        projection = project_investment_growth(
            current_value=0.0,
            monthly_contribution=1000.0,
            months=12,
            annual_return=0.0,
        )
        
        assert len(projection) == 13
        assert projection[0] == 0.0
        assert projection[12] == 12000.0
        assert projection[6] == 6000.0
    
    def test_with_return(self):
        """Growth with both return and contributions."""
        projection = project_investment_growth(
            current_value=10000.0,
            monthly_contribution=100.0,
            months=12,
            annual_return=0.12,  # 1% monthly
        )
        
        # Check growth is positive
        assert projection[12] > projection[0]
        # Check monotonic increase
        for i in range(len(projection) - 1):
            assert projection[i+1] >= projection[i]
    
    def test_array_length(self):
        """Array length is months + 1 (including month 0)."""
        for months in [1, 12, 120]:
            projection = project_investment_growth(
                10000.0, 100.0, months, 0.07
            )
            assert len(projection) == months + 1
    
    def test_zero_months(self):
        """Zero months -> array with just starting value."""
        projection = project_investment_growth(
            10000.0, 100.0, 0, 0.07
        )
        assert len(projection) == 1
        assert projection[0] == 10000.0


# ============================================================================
# HEALTH SCORE TESTS
# ============================================================================

class TestHealthScore:
    """Test compute_financial_health_score()"""
    
    def test_perfect_score(self):
        """All ideal metrics -> 100."""
        metrics = {
            'savings_rate': 50.0,  # Very high
            'emergency_fund_months': 6.0,  # Ideal
            'debt_to_income_ratio': 0.05,  # Excellent
            'investment_ratio': 0.5,  # High
        }
        score = compute_financial_health_score(metrics)
        assert score >= 90
    
    def test_poor_score(self):
        """All poor metrics -> low score."""
        metrics = {
            'savings_rate': 0.0,  # Zero savings
            'emergency_fund_months': 0.0,  # No emergency fund
            'debt_to_income_ratio': 1.0,  # Very high debt
            'investment_ratio': 0.0,  # No investments
        }
        score = compute_financial_health_score(metrics)
        assert score < 30
    
    def test_missing_keys_default_to_zero(self):
        """Missing metrics default to worst case."""
        metrics = {}
        score = compute_financial_health_score(metrics)
        assert score == 0
    
    def test_partial_metrics(self):
        """Mix of good and bad metrics."""
        metrics = {
            'savings_rate': 30.0,  # Good
            'debt_to_income_ratio': 0.40,  # Poor
            # Others default to zero
        }
        score = compute_financial_health_score(metrics)
        assert 0 < score < 100
    
    def test_score_in_range(self):
        """Score always in [0, 100]."""
        test_cases = [
            {},
            {'savings_rate': 100.0},
            {'debt_to_income_ratio': 2.0},
            {'emergency_fund_months': 20.0},
            {
                'savings_rate': 50.0,
                'emergency_fund_months': 5.0,
                'debt_to_income_ratio': 0.2,
                'investment_ratio': 0.3,
            }
        ]
        
        for metrics in test_cases:
            score = compute_financial_health_score(metrics)
            assert 0 <= score <= 100


# ============================================================================
# GOAL METRICS TESTS
# ============================================================================

class TestGoalMetrics:
    """Test compute_goal_metrics()"""
    
    def test_already_achieved(self):
        """Current >= target -> already achieved."""
        result = compute_goal_metrics(
            goal_target=10000.0,
            goal_current=10000.0,
            goal_monthly_increment=100.0,
            months_remaining=12,
            expected_annual_return=0.07,
        )
        
        assert result['remaining_amount'] == 0.0
        assert result['progress_percentage'] == 100.0
        assert result['achievable_with_planned_contribution'] is True
    
    def test_not_achievable(self):
        """Small increment, large gap -> not achievable."""
        result = compute_goal_metrics(
            goal_target=100000.0,
            goal_current=1000.0,
            goal_monthly_increment=1.0,  # Too small
            months_remaining=12,
            expected_annual_return=0.0,
        )
        
        assert result['achievable_with_planned_contribution'] is False
        assert result['projected_final_balance'] < result['target_amount']
    
    def test_achievable_with_good_plan(self):
        """Sufficient increment -> achievable."""
        result = compute_goal_metrics(
            goal_target=10000.0,
            goal_current=0.0,
            goal_monthly_increment=900.0,
            months_remaining=12,
            expected_annual_return=0.0,
        )
        
        assert result['achievable_with_planned_contribution'] is True
        assert result['projected_final_balance'] >= result['target_amount']


# ============================================================================
# NUMERICAL STABILITY TESTS
# ============================================================================

class TestNumericalStability:
    """Test numerical consistency and edge cases"""
    
    def test_determinism(self):
        """Repeated calls with same input give same output."""
        args = (100000.0, 10000.0, 120, 0.07)
        
        result1 = compute_required_sip(*args)
        result2 = compute_required_sip(*args)
        
        assert result1 == result2  # Exact match
    
    def test_very_large_numbers(self):
        """Handles large monetary values without overflow."""
        sip = compute_required_sip(
            target_amount=1e9,  # $1 billion
            current_value=1e8,  # $100 million
            months=300,
            expected_annual_return=0.05,
        )
        
        assert sip > 0
        assert sip < 1e9  # Sanity check
    
    def test_very_small_numbers(self):
        """Handles very small amounts."""
        rate = compute_savings_rate(
            monthly_income=0.01,
            monthly_savings=0.001,
        )
        
        assert 0 <= rate <= 100
    
    def test_floating_point_precision(self):
        """Rounding is consistent."""
        rate1 = compute_savings_rate(1.0, 0.333)
        rate2 = compute_savings_rate(1.0, 0.333)
        
        # Same rate to 2 decimal places
        assert rate1 == rate2
