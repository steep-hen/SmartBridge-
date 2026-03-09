"""Test Suite for Risk Simulation Module.

Tests for Monte Carlo portfolio simulation, scenarios, and analysis functions.

Run with: python -m pytest tests/test_risk_simulation.py -v
"""

import sys
import pytest
import numpy as np
from typing import Dict, Any

# Import risk simulation module
try:
    from backend.finance.risk_simulation import (
        run_monte_carlo_simulation,
        calculate_portfolio_percentiles,
        calculate_return_percentiles,
        calculate_drawdown_analysis,
        calculate_probability_of_loss,
        calculate_time_to_goal,
        sensitivity_analysis,
        compare_scenarios,
        SimulationInput,
        SimulationOutput,
    )
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def basic_params():
    """Basic simulation parameters."""
    return {
        'initial_investment': 100000,
        'monthly_sip': 5000,
        'expected_return': 0.12,
        'volatility': 0.15,
        'years': 10,
        'num_simulations': 1000,
    }


@pytest.fixture
def conservative_params():
    """Conservative investment parameters."""
    return {
        'initial_investment': 100000,
        'monthly_sip': 3000,
        'expected_return': 0.08,
        'volatility': 0.10,
        'years': 10,
        'num_simulations': 1000,
    }


@pytest.fixture
def aggressive_params():
    """Aggressive investment parameters."""
    return {
        'initial_investment': 100000,
        'monthly_sip': 10000,
        'expected_return': 0.16,
        'volatility': 0.25,
        'years': 10,
        'num_simulations': 1000,
    }


# ============================================================================
# BASIC SIMULATION TESTS
# ============================================================================

class TestBasicSimulation:
    """Test basic Monte Carlo simulation functionality."""
    
    def test_simulation_runs_successfully(self, basic_params):
        """Test that simulation completes without errors."""
        result = run_monte_carlo_simulation(**basic_params)
        assert result is not None
        assert isinstance(result, SimulationOutput)
    
    def test_output_has_all_fields(self, basic_params):
        """Test that output contains all required fields."""
        result = run_monte_carlo_simulation(**basic_params)
        
        required_fields = [
            'final_values', 'portfolio_paths', 'monthly_values',
            'median_return', 'best_case', 'worst_case',
            'percentile_10', 'percentile_25', 'percentile_75', 'percentile_90',
            'mean_return', 'std_return', 'min_return', 'max_return',
            'success_probability', 'value_at_risk_95', 'sharpe_ratio',
            'cagr', 'final_balance', 'total_invested'
        ]
        
        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"
    
    def test_final_values_shape(self, basic_params):
        """Test that final_values array has correct shape."""
        result = run_monte_carlo_simulation(**basic_params)
        assert result.final_values.shape[0] == basic_params['num_simulations']
    
    def test_portfolio_paths_shape(self, basic_params):
        """Test that portfolio_paths has correct shape."""
        result = run_monte_carlo_simulation(**basic_params)
        expected_periods = basic_params['years'] * 12 + 1
        assert result.portfolio_paths.shape == (basic_params['num_simulations'], expected_periods)
    
    def test_final_balance_is_positive(self, basic_params):
        """Test that final balance is positive."""
        result = run_monte_carlo_simulation(**basic_params)
        assert result.final_balance > 0
        assert result.worst_case > 0
    
    def test_percentile_ordering(self, basic_params):
        """Test that percentiles follow correct ordering."""
        result = run_monte_carlo_simulation(**basic_params)
        
        assert result.worst_case <= result.percentile_10
        assert result.percentile_10 <= result.percentile_25
        assert result.percentile_25 <= result.final_balance
        assert result.final_balance <= result.percentile_75
        assert result.percentile_75 <= result.percentile_90
        assert result.percentile_90 <= result.best_case
    
    def test_return_statistics_reasonable(self, basic_params):
        """Test that return statistics are within reasonable ranges."""
        result = run_monte_carlo_simulation(**basic_params)
        
        # Mean return should be between worst and best
        assert result.worst_case <= result.mean_return <= result.best_case
        
        # Std dev should be positive
        assert result.std_return >= 0
        
        # Median return should be reasonable
        assert -100 <= result.median_return <= 500


# ============================================================================
# INPUT VALIDATION TESTS
# ============================================================================

class TestInputValidation:
    """Test input validation."""
    
    def test_negative_initial_investment_fails(self):
        """Test that negative initial investment raises error."""
        with pytest.raises(ValueError):
            run_monte_carlo_simulation(
                initial_investment=-100000,
                years=10
            )
    
    def test_negative_monthly_sip_fails(self):
        """Test that negative SIP raises error."""
        with pytest.raises(ValueError):
            run_monte_carlo_simulation(
                initial_investment=100000,
                monthly_sip=-5000,
                years=10
            )
    
    def test_negative_volatility_fails(self):
        """Test that negative volatility raises error."""
        with pytest.raises(ValueError):
            run_monte_carlo_simulation(
                initial_investment=100000,
                volatility=-0.15,
                years=10
            )
    
    def test_invalid_years_fails(self):
        """Test that invalid year range fails."""
        with pytest.raises(ValueError):
            run_monte_carlo_simulation(
                initial_investment=100000,
                years=0
            )
        
        with pytest.raises(ValueError):
            run_monte_carlo_simulation(
                initial_investment=100000,
                years=100
            )
    
    def test_invalid_num_simulations_fails(self):
        """Test that invalid simulation count fails."""
        with pytest.raises(ValueError):
            run_monte_carlo_simulation(
                initial_investment=100000,
                num_simulations=50
            )


# ============================================================================
# STATISTICAL PROPERTIES TESTS
# ============================================================================

class TestStatisticalProperties:
    """Test statistical properties of simulation results."""
    
    def test_higher_volatility_wider_distribution(self):
        """Test that higher volatility produces wider outcome distribution."""
        low_vol = run_monte_carlo_simulation(
            initial_investment=100000,
            years=10,
            volatility=0.10,
            num_simulations=1000,
            seed=42
        )
        
        high_vol = run_monte_carlo_simulation(
            initial_investment=100000,
            years=10,
            volatility=0.30,
            num_simulations=1000,
            seed=42
        )
        
        # Wider distribution (higher std)
        assert high_vol.std_return > low_vol.std_return
    
    def test_higher_return_higher_outcomes(self):
        """Test that higher expected return produces higher median outcome."""
        low_return = run_monte_carlo_simulation(
            initial_investment=100000,
            years=10,
            expected_return=0.08,
            volatility=0.15,
            num_simulations=1000,
            seed=42
        )
        
        high_return = run_monte_carlo_simulation(
            initial_investment=100000,
            years=10,
            expected_return=0.16,
            volatility=0.15,
            num_simulations=1000,
            seed=42
        )
        
        # Higher return should give higher median
        assert high_return.final_balance > low_return.final_balance
    
    def test_longer_period_higher_returns(self):
        """Test that longer investment period produces higher returns."""
        short_term = run_monte_carlo_simulation(
            initial_investment=100000,
            years=5,
            expected_return=0.12,
            volatility=0.15,
            num_simulations=1000,
            seed=42
        )
        
        long_term = run_monte_carlo_simulation(
            initial_investment=100000,
            years=20,
            expected_return=0.12,
            volatility=0.15,
            num_simulations=1000,
            seed=42
        )
        
        # Longer period should give higher final balance
        assert long_term.final_balance > short_term.final_balance
    
    def test_sip_increases_final_balance(self):
        """Test that monthly SIP increases final balance."""
        no_sip = run_monte_carlo_simulation(
            initial_investment=100000,
            monthly_sip=0,
            years=10,
            expected_return=0.12,
            volatility=0.15,
            num_simulations=1000,
            seed=42
        )
        
        with_sip = run_monte_carlo_simulation(
            initial_investment=100000,
            monthly_sip=5000,
            years=10,
            expected_return=0.12,
            volatility=0.15,
            num_simulations=1000,
            seed=42
        )
        
        # With SIP should have higher final balance
        assert with_sip.total_invested > no_sip.total_invested
        assert with_sip.final_balance > no_sip.final_balance


# ============================================================================
# ANALYSIS FUNCTIONS TESTS
# ============================================================================

class TestAnalysisFunctions:
    """Test analysis utility functions."""
    
    def test_portfolio_percentiles(self, basic_params):
        """Test portfolio percentile calculation."""
        result = run_monte_carlo_simulation(**basic_params)
        percentiles = calculate_portfolio_percentiles(result.final_values)
        
        assert isinstance(percentiles, dict)
        assert 5 in percentiles
        assert 50 in percentiles
        assert 95 in percentiles
        assert percentiles[5] <= percentiles[50] <= percentiles[95]
    
    def test_return_percentiles(self, basic_params):
        """Test return percentile calculation."""
        result = run_monte_carlo_simulation(**basic_params)
        percentiles = calculate_return_percentiles(
            result.final_values,
            result.total_invested
        )
        
        assert isinstance(percentiles, dict)
        assert percentiles[5] <= percentiles[50] <= percentiles[95]
    
    def test_drawdown_analysis(self, basic_params):
        """Test drawdown analysis."""
        result = run_monte_carlo_simulation(**basic_params)
        drawdown = calculate_drawdown_analysis(result.portfolio_paths)
        
        assert 'average_max_drawdown' in drawdown
        assert 'worst_max_drawdown' in drawdown
        assert 'median_max_drawdown' in drawdown
        
        # Drawdowns should be negative
        assert drawdown['worst_max_drawdown'] < 0
        assert drawdown['median_max_drawdown'] < 0
    
    def test_probability_of_loss(self, basic_params):
        """Test probability of loss calculation."""
        result = run_monte_carlo_simulation(**basic_params)
        prob_loss = calculate_probability_of_loss(
            result.final_values,
            result.total_invested
        )
        
        assert isinstance(prob_loss, float)
        assert 0 <= prob_loss <= 100
    
    def test_time_to_goal_analysis(self, basic_params):
        """Test time to goal analysis."""
        result = run_monte_carlo_simulation(**basic_params)
        goal_amount = result.total_invested * 2  # Double the investment
        
        time_analysis = calculate_time_to_goal(
            result.portfolio_paths,
            goal_amount,
            basic_params['years']
        )
        
        assert 'success_probability' in time_analysis
        assert 'median_months' in time_analysis
        assert 0 <= time_analysis['success_probability'] <= 100


# ============================================================================
# SCENARIO TESTS
# ============================================================================

class TestScenarios:
    """Test scenario comparison functionality."""
    
    def test_conservative_vs_aggressive(self):
        """Test conservative vs aggressive scenario comparison."""
        scenarios = {
            'Conservative': {
                'initial_investment': 100000,
                'monthly_sip': 3000,
                'expected_return': 0.08,
                'volatility': 0.10,
                'years': 10,
            },
            'Aggressive': {
                'initial_investment': 100000,
                'monthly_sip': 10000,
                'expected_return': 0.16,
                'volatility': 0.25,
                'years': 10,
            }
        }
        
        results = compare_scenarios(scenarios, num_simulations=500)
        
        assert 'Conservative' in results
        assert 'Aggressive' in results
        
        # Aggressive should have higher return potential
        assert results['Aggressive']['best_case'] > results['Conservative']['best_case']
    
    def test_scenario_results_have_all_metrics(self):
        """Test that scenario results contain all metrics."""
        scenarios = {
            'Test': {
                'initial_investment': 100000,
                'years': 10,
            }
        }
        
        results = compare_scenarios(scenarios, num_simulations=500)
        
        required_fields = [
            'median_return', 'worst_case', 'best_case',
            'final_balance', 'sharpe_ratio', 'success_probability'
        ]
        
        for field in required_fields:
            assert field in results['Test']


# ============================================================================
# SENSITIVITY ANALYSIS TESTS
# ============================================================================

class TestSensitivityAnalysis:
    """Test sensitivity analysis."""
    
    def test_sensitivity_analysis_runs(self):
        """Test that sensitivity analysis completes."""
        results = sensitivity_analysis(
            initial_investment=100000,
            monthly_sip=5000,
            years=10,
            returns=[0.10, 0.12],
            volatilities=[0.15, 0.20],
            num_simulations=500
        )
        
        assert len(results) == 4  # 2 returns × 2 volatilities
        assert (0.10, 0.15) in results
        assert (0.12, 0.20) in results
    
    def test_sensitivity_results_structure(self):
        """Test structure of sensitivity results."""
        results = sensitivity_analysis(
            initial_investment=100000,
            years=10,
            num_simulations=500
        )
        
        for key, metrics in results.items():
            assert isinstance(key, tuple)
            assert len(key) == 2  # (return, volatility)
            assert 'median_return' in metrics
            assert 'worst_case' in metrics
            assert 'best_case' in metrics


# ============================================================================
# REPRODUCIBILITY TESTS
# ============================================================================

class TestReproducibility:
    """Test reproducibility with seeds."""
    
    def test_same_seed_same_results(self, basic_params):
        """Test that same seed produces same results."""
        params1 = {**basic_params, 'seed': 123}
        params2 = {**basic_params, 'seed': 123}
        
        result1 = run_monte_carlo_simulation(**params1)
        result2 = run_monte_carlo_simulation(**params2)
        
        assert result1.final_balance == result2.final_balance
        assert result1.median_return == result2.median_return
        assert np.array_equal(result1.final_values, result2.final_values)
    
    def test_different_seed_different_results(self, basic_params):
        """Test that different seeds produce different results."""
        params1 = {**basic_params, 'seed': 123}
        params2 = {**basic_params, 'seed': 456}
        
        result1 = run_monte_carlo_simulation(**params1)
        result2 = run_monte_carlo_simulation(**params2)
        
        # Results should be different (with very high probability)
        assert result1.final_balance != result2.final_balance


# ============================================================================
# EDGE CASES TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_initial_investment(self):
        """Test with zero initial investment (SIP only)."""
        result = run_monte_carlo_simulation(
            initial_investment=0,
            monthly_sip=5000,
            years=10,
            num_simulations=500
        )
        
        assert result.final_balance > 0
        assert result.total_invested == 60000  # 5000 * 12 * 10
    
    def test_zero_volatility(self):
        """Test with zero volatility (deterministic)."""
        result = run_monte_carlo_simulation(
            initial_investment=100000,
            expected_return=0.10,
            volatility=0.0,
            years=10,
            num_simulations=100
        )
        
        # All simulations should have similar results (deterministic)
        assert result.std_return < 1  # Should be very low
    
    def test_short_investment_period(self):
        """Test with 1-year investment period."""
        result = run_monte_carlo_simulation(
            initial_investment=100000,
            years=1,
            num_simulations=500
        )
        
        assert result.portfolio_paths.shape[1] == 13  # 12 months + initial
    
    def test_long_investment_period(self):
        """Test with long investment period."""
        result = run_monte_carlo_simulation(
            initial_investment=100000,
            years=40,
            num_simulations=500
        )
        
        assert result.portfolio_paths.shape[1] == 481  # 40*12 + 1
        assert result.final_balance > result.total_invested


# ============================================================================
# PERFORMANCE METRICS TESTS
# ============================================================================

class TestPerformanceMetrics:
    """Test performance metric calculations."""
    
    def test_sharpe_ratio_positive_return(self):
        """Test Sharpe ratio with positive returns."""
        result = run_monte_carlo_simulation(
            initial_investment=100000,
            expected_return=0.15,
            volatility=0.15,
            years=10,
            num_simulations=1000
        )
        
        # Sharpe ratio should be positive for positive excess returns
        assert result.sharpe_ratio >= 0
    
    def test_cagr_reasonable_range(self):
        """Test CAGR is within reasonable range."""
        result = run_monte_carlo_simulation(
            initial_investment=100000,
            expected_return=0.12,
            years=10,
            num_simulations=500
        )
        
        # CAGR should be influenced by expected return
        assert 0 < result.cagr < 0.30
    
    def test_success_probability_range(self):
        """Test success probability is valid percentage."""
        result = run_monte_carlo_simulation(
            initial_investment=100000,
            years=10,
            num_simulations=500
        )
        
        assert 0 <= result.success_probability <= 100


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "🧪 RISK SIMULATION TEST SUITE 🧪".center(70))
    print()
    
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-ra'
    ])


if __name__ == "__main__":
    main()
