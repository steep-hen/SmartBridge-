"""Test Suite for Financial Forecasting Module.

Tests:
- Data preparation
- Prophet forecasting
- ARIMA forecasting
- Savings projections
- Scenario analysis
- API endpoints

Run with: python test_financial_forecast.py
"""

import sys
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
from typing import List, Dict, Any

# Import forecasting module
try:
    from backend.ml.financial_forecast import (
        prepare_transaction_data,
        forecast_with_prophet,
        forecast_with_arima,
        forecast_expenses_and_savings,
        analyze_scenarios,
        PROPHET_AVAILABLE,
        ARIMA_AVAILABLE,
    )
except ImportError:
    print("❌ Error: financial_forecast module not found")
    sys.exit(1)


# ============================================================================
# TEST DATA GENERATORS
# ============================================================================

def generate_test_transactions(days: int = 180) -> tuple:
    """Generate sample transactions for testing."""
    
    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    expenses = []
    income = []
    
    for current_date in dates:
        # Income on 1st of month
        if current_date.day == 1:
            income.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'amount': 50000,
                'type': 'income',
                'category': 'salary'
            })
        
        # Random daily expenses
        if np.random.random() > 0.5:
            amount = np.random.normal(1500, 500)
            amount = max(100, min(5000, amount))
            
            expenses.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'amount': round(amount, 2),
                'type': 'expense',
                'category': np.random.choice(['groceries', 'transport', 'entertainment', 'utilities'])
            })
    
    return expenses, income


# ============================================================================
# TEST SUITES
# ============================================================================

def test_data_preparation():
    """Test data preparation functions."""
    print("\n" + "="*70)
    print("TEST 1: Data Preparation")
    print("="*70)
    
    expenses, income = generate_test_transactions(180)
    print(f"\n✓ Generated {len(expenses)} expense transactions")
    print(f"✓ Generated {len(income)} income transactions")
    
    # Test daily aggregation
    df_daily = prepare_transaction_data(expenses, aggregation='daily')
    print(f"\n✓ Daily aggregation: {len(df_daily)} days of data")
    assert len(df_daily) > 0, "Should have daily data"
    assert 'ds' in df_daily.columns, "Should have 'ds' column"
    assert 'y' in df_daily.columns, "Should have 'y' column"
    
    # Test weekly aggregation
    df_weekly = prepare_transaction_data(expenses, aggregation='weekly')
    print(f"✓ Weekly aggregation: {len(df_weekly)} weeks of data")
    assert len(df_weekly) > 0, "Should have weekly data"
    
    # Test monthly aggregation
    df_monthly = prepare_transaction_data(expenses, aggregation='monthly')
    print(f"✓ Monthly aggregation: {len(df_monthly)} months of data")
    assert len(df_monthly) > 0, "Should have monthly data"
    
    print("\n✅ Data preparation tests passed")


def test_prophet_forecasting():
    """Test Prophet forecasting."""
    print("\n" + "="*70)
    print("TEST 2: Prophet Forecasting")
    print("="*70)
    
    if not PROPHET_AVAILABLE:
        print("⚠️  Prophet not available. Skipping test.")
        return
    
    try:
        expenses, _ = generate_test_transactions(180)
        df = prepare_transaction_data(expenses, aggregation='daily')
        
        print(f"\nForecasting with {len(df)} daily data points...")
        
        forecast_df, model_info = forecast_with_prophet(
            df,
            periods=180,
            interval_width=0.95,
            seasonality_mode='additive'
        )
        
        print(f"✓ Generated {len(forecast_df)} forecast periods")
        print(f"✓ Model: {model_info['model']}")
        print(f"✓ MAPE: {model_info['mape']:.2f}%")
        
        # Check forecast structure
        assert 'predicted' in forecast_df.columns, "Should have predicted column"
        assert 'lower_bound' in forecast_df.columns, "Should have lower_bound"
        assert 'upper_bound' in forecast_df.columns, "Should have upper_bound"
        
        # Check predictions are reasonable
        avg_predicted = forecast_df['predicted'].mean()
        print(f"✓ Average predicted expense: ₹{avg_predicted:,.0f}")
        
        assert forecast_df['predicted'].min() >= 0, "Predictions should be non-negative"
        assert forecast_df['upper_bound'].max() > forecast_df['predicted'].mean(), \
            "Upper bound should exceed mean"
        
        print("\n✅ Prophet forecasting tests passed")
        
    except Exception as e:
        print(f"❌ Prophet test failed: {str(e)}")
        raise


def test_arima_forecasting():
    """Test ARIMA forecasting."""
    print("\n" + "="*70)
    print("TEST 3: ARIMA Forecasting")
    print("="*70)
    
    if not ARIMA_AVAILABLE:
        print("⚠️  ARIMA not available. Skipping test.")
        return
    
    try:
        expenses, _ = generate_test_transactions(180)
        df = prepare_transaction_data(expenses, aggregation='daily')
        
        print(f"\nForecasting with {len(df)} daily data points...")
        
        forecast_df, model_info = forecast_with_arima(
            df,
            periods=90,
            order=(1, 1, 1)
        )
        
        print(f"✓ Generated {len(forecast_df)} forecast periods")
        print(f"✓ Model: {model_info['model']}")
        print(f"✓ ARIMA Order: {model_info['order']}")
        print(f"✓ AIC: {model_info['aic']:.2f}")
        
        # Check structure
        assert len(forecast_df) > 0, "Should have forecast data"
        assert 'predicted' in forecast_df.columns, "Should have predictions"
        
        print("\n✅ ARIMA forecasting tests passed")
        
    except Exception as e:
        print(f"❌ ARIMA test failed: {str(e)}")
        raise


def test_savings_projection():
    """Test savings projection."""
    print("\n" + "="*70)
    print("TEST 4: Savings Projection")
    print("="*70)
    
    if not PROPHET_AVAILABLE and not ARIMA_AVAILABLE:
        print("⚠️  No forecasting model available. Skipping test.")
        return
    
    try:
        expenses, income = generate_test_transactions(180)
        
        print("\nGenerating full forecast with savings projection...")
        
        result = forecast_expenses_and_savings(
            expense_transactions=expenses,
            income_transactions=income,
            model_type='prophet' if PROPHET_AVAILABLE else 'arima',
            forecast_months=6,
            starting_balance=10000,
            aggregation='daily'
        )
        
        # Check structure
        assert 'predicted_expenses_next_6_months' in result
        assert 'savings_projection' in result
        assert 'summary' in result
        
        print(f"\n✓ Forecasted {len(result['predicted_expenses_next_6_months'])} months")
        
        # Check savings projection
        savings = result['savings_projection']
        assert 'monthly_savings' in savings
        assert 'average_monthly_savings' in savings
        assert 'projected_balance' in savings
        
        monthly_data = savings['monthly_savings']
        print(f"✓ Generated {len(monthly_data)} months of savings data")
        
        for month_data in monthly_data[:2]:
            print(f"  {month_data['month']}: Income ₹{month_data['income']:,.0f} " +
                  f"- Expenses ₹{month_data['expenses']:,.0f} " +
                  f"= Savings ₹{month_data['savings']:,.0f}")
        
        print(f"\n✓ Average monthly savings: ₹{savings['average_monthly_savings']:,.0f}")
        print(f"✓ Projected balance: ₹{savings['projected_balance']:,.0f}")
        print(f"✓ Savings trend: {savings['savings_trend']}")
        
        # Check consistency
        assert savings['average_monthly_savings'] > 0, "Should have positive average savings"
        
        print("\n✅ Savings projection tests passed")
        
    except Exception as e:
        print(f"❌ Savings projection test failed: {str(e)}")
        raise


def test_scenario_analysis():
    """Test scenario analysis."""
    print("\n" + "="*70)
    print("TEST 5: Scenario Analysis")
    print("="*70)
    
    if not PROPHET_AVAILABLE and not ARIMA_AVAILABLE:
        print("⚠️  No forecasting model available. Skipping test.")
        return
    
    try:
        expenses, income = generate_test_transactions(180)
        
        # Generate baseline forecast
        baseline = forecast_expenses_and_savings(
            expense_transactions=expenses,
            income_transactions=income,
            model_type='prophet' if PROPHET_AVAILABLE else 'arima',
            forecast_months=6,
            starting_balance=10000,
            aggregation='daily'
        )
        
        # Analyze scenarios
        scenarios = analyze_scenarios(
            baseline_forecast=baseline,
            expense_increase_percent=10,
            income_increase_percent=5
        )
        
        print("\n✓ Scenarios analyzed:")
        print(f"  Baseline: ₹{scenarios['baseline_monthly_savings']:,.0f}/month")
        print(f"  Best case: ₹{scenarios['best_case_monthly_savings']:,.0f}/month")
        print(f"  Worst case: ₹{scenarios['worst_case_monthly_savings']:,.0f}/month")
        
        assert scenarios['baseline_monthly_savings'] > 0
        assert scenarios['best_case_monthly_savings'] > scenarios['baseline_monthly_savings']
        assert scenarios['worst_case_monthly_savings'] < scenarios['baseline_monthly_savings']
        
        print("\n✅ Scenario analysis tests passed")
        
    except Exception as e:
        print(f"❌ Scenario analysis test failed: {str(e)}")
        raise


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*70)
    print("TEST 6: Edge Cases & Error Handling")
    print("="*70)
    
    print("\n✓ Testing empty transaction handling...")
    try:
        forecast_expenses_and_savings(
            expense_transactions=[],
            income_transactions=[{'date': '2024-01-01', 'amount': 5000, 'type': 'income'}]
        )
        assert False, "Should raise error for empty expenses"
    except ValueError:
        print("  ✓ Empty expenses handled correctly")
    
    print("✓ Testing insufficient data...")
    try:
        small_expenses = [{'date': '2024-01-01', 'amount': 1000, 'type': 'expense'}]
        small_income = [{'date': '2024-01-01', 'amount': 5000, 'type': 'income'}]
        
        if PROPHET_AVAILABLE:
            forecast_expenses_and_savings(
                expense_transactions=small_expenses,
                income_transactions=small_income,
                model_type='prophet'
            )
            assert False, "Should raise error for insufficient data"
    except ValueError:
        print("  ✓ Insufficient data handled correctly")
    
    print("✓ Testing negative amounts...")
    expenses = [
        {'date': '2024-01-01', 'amount': -1000, 'type': 'expense'},
        {'date': '2024-01-02', 'amount': 500, 'type': 'expense'}
    ]
    df = prepare_transaction_data(expenses)
    # Negative should be converted to positive
    assert df['y'].min() >= 0, "Amounts should be non-negative"
    print("  ✓ Negative amounts converted correctly")
    
    print("\n✅ Edge case tests passed")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "🧪 FINANCIAL FORECAST MODULE TEST SUITE 🧪".center(70))
    print()
    
    # Check available models
    print("Available Models:")
    print(f"  Prophet: {'✓ Available' if PROPHET_AVAILABLE else '✗ Not available'}")
    print(f"  ARIMA: {'✓ Available' if ARIMA_AVAILABLE else '✗ Not available'}")
    
    if not PROPHET_AVAILABLE and not ARIMA_AVAILABLE:
        print("\n❌ Error: No forecasting models available!")
        print("Install with: pip install prophet statsmodels")
        return
    
    try:
        test_data_preparation()
        test_prophet_forecasting()
        test_arima_forecasting()
        test_savings_projection()
        test_scenario_analysis()
        test_edge_cases()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!".center(70))
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
