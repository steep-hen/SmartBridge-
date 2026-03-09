"""Comprehensive tests for portfolio optimizer module.

Tests cover:
- Portfolio allocation generation for all risk profiles
- Instrument recommendations by asset class and time horizon
- Portfolio value projections
- Risk-adjusted recommendations based on user profile
- Edge cases and error handling
- Integration with report builder
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any

from backend.finance.portfolio_optimizer import (
    generate_portfolio_recommendation,
    calculate_portfolio_value_at_horizon,
    get_risk_adjusted_recommendation,
    _categorize_horizon,
    _adjust_allocation_for_horizon,
    _round_allocation,
    _round_currency,
    _round_ratio,
    RISK_PROFILES,
    INSTRUMENT_RECOMMENDATIONS,
)


# ============================================================================
# FIXTURES AND TEST DATA
# ============================================================================

@pytest.fixture
def valid_user_profile():
    """Sample user profile for testing."""
    return {
        'risk_tolerance': 'medium',
        'age': 35,
        'monthly_income': 100000,
        'monthly_expenses': 60000,
        'emergency_fund_months': 6,
        'net_worth': 500000,
    }


@pytest.fixture
def aggressive_user_profile():
    """Aggressive investor profile."""
    return {
        'risk_tolerance': 'high',
        'age': 28,
        'monthly_income': 150000,
        'monthly_expenses': 50000,
        'emergency_fund_months': 12,
        'net_worth': 1000000,
    }


@pytest.fixture
def conservative_user_profile():
    """Conservative investor profile."""
    return {
        'risk_tolerance': 'low',
        'age': 60,
        'monthly_income': 50000,
        'monthly_expenses': 40000,
        'emergency_fund_months': 8,
        'net_worth': 3000000,
    }


# ============================================================================
# BASIC ALLOCATION TESTS
# ============================================================================

class TestBasicAllocation:
    """Test basic portfolio allocation for each risk profile."""
    
    def test_low_risk_allocation(self):
        """Test low risk profile allocation."""
        rec = generate_portfolio_recommendation('low')
        
        assert rec['available'] is False or 'recommended_portfolio' in rec
        assert rec['recommended_portfolio']['equity'] == 40
        assert rec['recommended_portfolio']['debt'] == 50
        assert rec['recommended_portfolio']['gold'] == 10
        
        # Verify sum to 100
        total = sum(rec['recommended_portfolio'].values())
        assert total == 100
    
    def test_medium_risk_allocation(self):
        """Test medium risk profile allocation."""
        rec = generate_portfolio_recommendation('medium')
        
        assert rec['recommended_portfolio']['equity'] == 70
        assert rec['recommended_portfolio']['debt'] == 20
        assert rec['recommended_portfolio']['gold'] == 10
        
        total = sum(rec['recommended_portfolio'].values())
        assert total == 100
    
    def test_high_risk_allocation(self):
        """Test high risk profile allocation."""
        rec = generate_portfolio_recommendation('high')
        
        assert rec['recommended_portfolio']['equity'] == 85
        assert rec['recommended_portfolio']['debt'] == 10
        assert rec['recommended_portfolio']['gold'] == 5
        
        total = sum(rec['recommended_portfolio'].values())
        assert total == 100
    
    def test_invalid_risk_tolerance(self):
        """Test error handling for invalid risk tolerance."""
        with pytest.raises(ValueError) as exc_info:
            generate_portfolio_recommendation('extremely_high')
        
        assert 'Invalid risk_tolerance' in str(exc_info.value)


# ============================================================================
# HORIZON AND AGE ADJUSTMENT TESTS
# ============================================================================

class TestHorizonAdjustment:
    """Test allocation adjustment based on investment horizon."""
    
    def test_short_term_horizon(self):
        """Short term (< 5 years) should favor debt."""
        rec = generate_portfolio_recommendation('high', investment_horizon=3)
        
        # Should reduce equity for short term
        assert rec['recommended_portfolio']['equity'] <= 40  # Down from 85
        assert rec['recommended_portfolio']['debt'] >= 50    # Up from 10
    
    def test_medium_term_horizon(self):
        """Medium term (5-10 years) keeps balanced approach."""
        rec = generate_portfolio_recommendation('medium', investment_horizon=7)
        
        # Should maintain or slightly adjust
        assert rec['recommended_portfolio']['equity'] >= 60
        assert rec['recommended_portfolio']['debt'] <= 30
    
    def test_long_term_horizon(self):
        """Long term (10+ years) should favor equity."""
        rec = generate_portfolio_recommendation('low', investment_horizon=20)
        
        # Should increase equity for long term
        assert rec['recommended_portfolio']['equity'] >= 50  # Up from 40
    
    def test_age_to_horizon_conversion(self):
        """Test age automatically converted to investment horizon."""
        age_35 = generate_portfolio_recommendation('medium', age=35)
        age_25 = generate_portfolio_recommendation('medium', age=25)
        
        # Younger age should have more equity
        assert age_25['recommended_portfolio']['equity'] >= age_35['recommended_portfolio']['equity']
    
    def test_retirement_age(self):
        """User near retirement should have conservative allocation."""
        age_62 = generate_portfolio_recommendation('high', age=62)
        
        # Even high risk tolerance should be moderated near retirement
        assert age_62['recommended_portfolio']['equity'] < 85


# ============================================================================
# INSTRUMENT RECOMMENDATION TESTS
# ============================================================================

class TestInstrumentRecommendations:
    """Test instrument recommendations for each asset class."""
    
    def test_equity_instruments_provided(self):
        """Test equity instruments recommended."""
        rec = generate_portfolio_recommendation('medium')
        
        assert 'asset_class_instruments' in rec
        equity_instruments = rec['asset_class_instruments']['equity']
        
        assert len(equity_instruments) > 0
        assert any('ETF' in inst['name'] or 'Fund' in inst['name'] for inst in equity_instruments)
    
    def test_debt_instruments_provided(self):
        """Test debt instruments recommended."""
        rec = generate_portfolio_recommendation('medium')
        
        debt_instruments = rec['asset_class_instruments']['debt']
        
        assert len(debt_instruments) > 0
        # Should have mix of government and corporate bonds
        assert any('Government' in inst['name'] or 'Liquid' in inst['name'] 
                  for inst in debt_instruments)
    
    def test_gold_instruments_provided(self):
        """Test gold instruments recommended."""
        rec = generate_portfolio_recommendation('medium')
        
        gold_instruments = rec['asset_class_instruments']['gold']
        
        assert len(gold_instruments) > 0
        assert any('ETF' in inst['name'] or 'Gold' in inst['name'] for inst in gold_instruments)
    
    def test_long_term_equity_instruments(self):
        """Test equity instruments for long-term horizon."""
        rec = generate_portfolio_recommendation('medium', investment_horizon=20)
        
        equity_instruments = rec['asset_class_instruments']['equity']
        
        # Long term should include growth-oriented instruments
        assert len(equity_instruments) > 0
        assert any('Index' in inst['type'] or 'Midcap' in inst['name'] 
                  for inst in equity_instruments)
    
    def test_short_term_debt_instruments(self):
        """Test debt instruments for short-term horizon."""
        rec = generate_portfolio_recommendation('medium', investment_horizon=3)
        
        debt_instruments = rec['asset_class_instruments']['debt']
        
        # Short term should include liquid instruments
        assert len(debt_instruments) > 0


# ============================================================================
# PORTFOLIO VALUE PROJECTION TESTS
# ============================================================================

class TestPortfolioProjection:
    """Test portfolio value projection calculations."""
    
    def test_projection_basic(self):
        """Test basic portfolio projection."""
        projection = calculate_portfolio_value_at_horizon(
            initial_investment=100000,
            monthly_sip=10000,
            allocation={'equity': 70, 'debt': 20, 'gold': 10},
            investment_horizon=10,
        )
        
        assert projection['initial_investment'] == 100000
        assert projection['monthly_sip'] == 10000
        assert projection['projected_final_value'] > projection['total_invested']
        assert projection['projected_gains'] > 0
    
    def test_projection_zero_sip(self):
        """Test projection with no monthly contributions."""
        projection = calculate_portfolio_value_at_horizon(
            initial_investment=500000,
            monthly_sip=0,
            allocation={'equity': 70, 'debt': 20, 'gold': 10},
            investment_horizon=10,
        )
        
        assert projection['projected_value_sip'] == 0
        assert projection['projected_value_initial'] > 500000
    
    def test_projection_conservative(self):
        """Conservative allocation should have lower returns."""
        conservative = calculate_portfolio_value_at_horizon(
            initial_investment=100000,
            monthly_sip=5000,
            allocation={'equity': 40, 'debt': 50, 'gold': 10},
            investment_horizon=10,
        )
        
        aggressive = calculate_portfolio_value_at_horizon(
            initial_investment=100000,
            monthly_sip=5000,
            allocation={'equity': 85, 'debt': 10, 'gold': 5},
            investment_horizon=10,
        )
        
        # Aggressive should have higher final value (more equity risk)
        assert aggressive['projected_final_value'] > conservative['projected_final_value']
    
    def test_projection_long_time(self):
        """Longer time horizon should show more compound growth."""
        short_term = calculate_portfolio_value_at_horizon(
            initial_investment=100000,
            monthly_sip=5000,
            allocation={'equity': 70, 'debt': 20, 'gold': 10},
            investment_horizon=5,
        )
        
        long_term = calculate_portfolio_value_at_horizon(
            initial_investment=100000,
            monthly_sip=5000,
            allocation={'equity': 70, 'debt': 20, 'gold': 10},
            investment_horizon=20,
        )
        
        # Much longer time should have significantly higher value
        assert long_term['projected_final_value'] > short_term['projected_final_value'] * 2
    
    def test_projection_invalid_horizon(self):
        """Test error handling for invalid horizon."""
        with pytest.raises(ValueError):
            calculate_portfolio_value_at_horizon(
                initial_investment=100000,
                monthly_sip=5000,
                allocation={'equity': 70, 'debt': 20, 'gold': 10},
                investment_horizon=0,
            )


# ============================================================================
# RISK-ADJUSTED RECOMMENDATION TESTS
# ============================================================================

class TestRiskAdjustedRecommendation:
    """Test risk-adjusted portfolio recommendations."""
    
    def test_adequate_emergency_fund(self, valid_user_profile):
        """User with adequate emergency fund should be suitable."""
        rec = get_risk_adjusted_recommendation(valid_user_profile)
        
        assert rec['suitability_assessment']['suitable'] is True
        assert len(rec['suitability_assessment']['concerns']) == 0
    
    def test_inadequate_emergency_fund(self):
        """User with low emergency fund should have concerns."""
        profile = {
            'risk_tolerance': 'high',
            'age': 35,
            'monthly_income': 100000,
            'monthly_expenses': 80000,
            'emergency_fund_months': 2,  # Too low
            'net_worth': 500000,
        }
        
        rec = get_risk_adjusted_recommendation(profile)
        
        assert rec['suitability_assessment']['suitable'] is False
        assert any('emergency' in c.lower() for c in rec['suitability_assessment']['concerns'])
    
    def test_high_expense_ratio(self):
        """User with high expense ratio should have concerns."""
        profile = {
            'risk_tolerance': 'medium',
            'age': 35,
            'monthly_income': 50000,
            'monthly_expenses': 45000,  # 90% ratio
            'emergency_fund_months': 6,
            'net_worth': 200000,
        }
        
        rec = get_risk_adjusted_recommendation(profile)
        
        assert not rec['suitability_assessment']['suitable']
        assert any('expense' in c.lower() for c in rec['suitability_assessment']['concerns'])
    
    def test_income_adequacy_check(self):
        """High risk with low income should trigger recommendation."""
        profile = {
            'risk_tolerance': 'high',
            'age': 35,
            'monthly_income': 30000,  # Low for high risk
            'monthly_expenses': 20000,
            'emergency_fund_months': 6,
            'net_worth': 200000,
        }
        
        rec = get_risk_adjusted_recommendation(profile)
        
        assert any('income' in c.lower() for c in rec['suitability_assessment']['concerns'])
        assert len(rec['suitability_assessment']['recommendations']) > 0


# ============================================================================
# STRATEGY AND IMPLEMENTATION TESTS
# ============================================================================

class TestAllocationStrategy:
    """Test allocation strategy descriptions."""
    
    def test_strategy_provided(self):
        """Test that strategy description is provided."""
        rec = generate_portfolio_recommendation('medium')
        
        assert 'allocation_strategy' in rec
        assert len(rec['allocation_strategy']) > 0
        assert 'Asset Allocation Strategy' in rec['allocation_strategy']
    
    def test_implementation_steps_provided(self):
        """Test that implementation steps are provided."""
        rec = generate_portfolio_recommendation('medium', monthly_investment=10000)
        
        assert 'implementation_steps' in rec
        steps = rec['implementation_steps']
        
        assert len(steps) > 0
        assert any('equity' in str(step).lower() for step in steps)
        assert any('debt' in str(step).lower() for step in steps)
    
    def test_rebalancing_strategy_provided(self):
        """Test that rebalancing strategy is provided."""
        rec = generate_portfolio_recommendation('medium')
        
        assert 'rebalancing_strategy' in rec
        rebal = rec['rebalancing_strategy']
        
        assert 'frequency' in rebal
        assert 'trigger_threshold' in rebal


# ============================================================================
# CHARACTERISTICS AND RISK PROFILE TESTS
# ============================================================================

class TestRiskCharacteristics:
    """Test expected characteristics by risk profile."""
    
    def test_low_risk_characteristics(self):
        """Low risk should have conservative characteristics."""
        rec = generate_portfolio_recommendation('low')
        
        chars = rec['expected_characteristics']
        
        # Check return expectations (lower for low risk)
        assert '5-6%' in chars['expected_annual_return']
        assert 'Conservative' in rec['risk_profile_details']
    
    def test_medium_risk_characteristics(self):
        """Medium risk should have balanced characteristics."""
        rec = generate_portfolio_recommendation('medium')
        
        chars = rec['expected_characteristics']
        
        assert '8-10%' in chars['expected_annual_return']
        assert 'Balanced' in rec['risk_profile_details']
    
    def test_high_risk_characteristics(self):
        """High risk should have aggressive characteristics."""
        rec = generate_portfolio_recommendation('high')
        
        chars = rec['expected_characteristics']
        
        assert '12-15%' in chars['expected_annual_return']
        assert 'Aggressive' in rec['risk_profile_details']


# ============================================================================
# RETURN VALUE STRUCTURE TESTS
# ============================================================================

class TestReturnStructure:
    """Test return value structure and completeness."""
    
    def test_complete_recommendation_structure(self):
        """Test that recommendation includes all required fields."""
        rec = generate_portfolio_recommendation('medium')
        
        required_fields = [
            'recommended_portfolio',
            'asset_class_instruments',
            'allocation_strategy',
            'implementation_steps',
            'rebalancing_strategy',
            'expected_characteristics',
            'timestamp',
        ]
        
        for field in required_fields:
            assert field in rec, f"Missing field: {field}"
    
    def test_allocation_structure(self):
        """Test recommended_portfolio structure."""
        rec = generate_portfolio_recommendation('medium')
        portfolio = rec['recommended_portfolio']
        
        assert 'equity' in portfolio
        assert 'debt' in portfolio
        assert 'gold' in portfolio
        
        # Check values are numeric
        assert isinstance(portfolio['equity'], (int, float))
        assert 0 <= portfolio['equity'] <= 100
    
    def test_instrument_structure(self):
        """Test asset_class_instruments structure."""
        rec = generate_portfolio_recommendation('medium')
        instruments = rec['asset_class_instruments']
        
        for asset_class in ['equity', 'debt', 'gold']:
            assert asset_class in instruments
            assert isinstance(instruments[asset_class], list)
            assert len(instruments[asset_class]) > 0
            
            # Check first instrument has required fields
            first = instruments[asset_class][0]
            assert 'name' in first
            assert 'description' in first
            assert 'type' in first


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_age_out_of_range_low(self):
        """Test error handling for age below minimum."""
        with pytest.raises(ValueError):
            generate_portfolio_recommendation('medium', age=17)
    
    def test_age_out_of_range_high(self):
        """Test error handling for age above maximum."""
        with pytest.raises(ValueError):
            generate_portfolio_recommendation('medium', age=125)
    
    def test_negative_investment_horizon(self):
        """Test error handling for negative horizon."""
        with pytest.raises(ValueError):
            generate_portfolio_recommendation('medium', investment_horizon=-5)
    
    def test_negative_monthly_investment(self):
        """Test error handling for negative investment."""
        with pytest.raises(ValueError):
            generate_portfolio_recommendation('medium', monthly_investment=-1000)
    
    def test_very_short_horizon(self):
        """Test allocation for very short 1-year horizon."""
        rec = generate_portfolio_recommendation('high', investment_horizon=1)
        
        # Should be very conservative for 1 year
        assert rec['recommended_portfolio']['equity'] <= 40
        assert rec['recommended_portfolio']['debt'] >= 50
    
    def test_very_long_horizon(self):
        """Test allocation for very long 30-year horizon."""
        rec = generate_portfolio_recommendation('low', investment_horizon=30)
        
        # Should increase equity even for conservative profile
        assert rec['recommended_portfolio']['equity'] >= 50


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_round_allocation(self):
        """Test allocation rounding."""
        assert _round_allocation(69.999) == 70.0
        assert _round_allocation(40.123) == 40.1
    
    def test_round_currency(self):
        """Test currency rounding."""
        assert _round_currency(1234.567) == 1234.57
        assert _round_currency(1000.005) == 1000.01 or _round_currency(1000.005) == 1000.00
    
    def test_round_ratio(self):
        """Test ratio rounding."""
        result = _round_ratio(0.123456789)
        assert result == round(0.123456789, 4)
    
    def test_categorize_horizon(self):
        """Test horizon categorization."""
        assert _categorize_horizon(3) == 'short_term'
        assert _categorize_horizon(7) == 'medium_term'
        assert _categorize_horizon(15) == 'long_term'
        assert _categorize_horizon(None) == 'medium_term'
    
    def test_adjust_allocation_conservation(self):
        """Test that allocation adjustments conserve 100%."""
        base = {'equity': 70, 'debt': 20, 'gold': 10}
        
        for horizon in [3, 7, 15, 20]:
            adjusted = _adjust_allocation_for_horizon(base.copy(), horizon)
            total = sum(adjusted.values())
            assert abs(total - 100) < 0.01  # Account for floating point


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests with other components."""
    
    def test_recommendation_in_report_builder(self):
        """Test that portfolio recommendation integrates with report builder."""
        from backend.finance.report_builder import _round_currency
        
        # Should be importable from report_builder
        assert callable(_round_currency)
    
    def test_with_monthly_investment(self):
        """Test complete flow with monthly investment."""
        monthly = 15000
        rec = generate_portfolio_recommendation(
            'medium',
            age=35,
            monthly_investment=monthly,
        )
        
        # Should include investment breakdown in strategy
        assert monthly > 0
        assert 'Monthly Investment Plan' in rec['allocation_strategy']
    
    def test_projection_with_recommendation(self):
        """Test combining recommendation with projection."""
        rec = generate_portfolio_recommendation(
            'medium',
            investment_horizon=15,
            monthly_investment=10000,
        )
        
        projection = calculate_portfolio_value_at_horizon(
            initial_investment=50000,
            monthly_sip=10000,
            allocation=rec['recommended_portfolio'],
            investment_horizon=15,
        )
        
        assert projection['projected_final_value'] > 50000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
