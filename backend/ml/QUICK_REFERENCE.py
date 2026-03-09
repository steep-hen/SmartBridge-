"""Quick Reference Guide for Financial Forecasting Module.

Copy-paste examples for common use cases.
"""

# ============================================================================
# QUICK REFERENCE: Common Usage Patterns
# ============================================================================

# 1. BASIC FORECAST GENERATION
# ============================================================================

from backend.ml.financial_forecast import forecast_expenses_and_savings

# Sample transaction data
expenses = [
    {'date': '2024-01-15', 'amount': 2500, 'category': 'groceries', 'type': 'expense'},
    {'date': '2024-01-16', 'amount': 150, 'category': 'transport', 'type': 'expense'},
    {'date': '2024-01-17', 'amount': 500, 'category': 'entertainment', 'type': 'expense'},
]

income = [
    {'date': '2024-01-01', 'amount': 50000, 'category': 'salary', 'type': 'income'},
    {'date': '2024-02-01', 'amount': 50000, 'category': 'salary', 'type': 'income'},
]

# Generate forecast
result = forecast_expenses_and_savings(
    expense_transactions=expenses,
    income_transactions=income,
    model_type='prophet',
    forecast_months=6,
    starting_balance=10000
)

# Access results
predicted_expenses = result['predicted_expenses_next_6_months']
savings = result['savings_projection']
print(f"Projected balance in 6 months: ₹{savings['projected_balance']:,.0f}")


# 2. API ENDPOINT IMPLEMENTATION
# ============================================================================

from flask import Flask, request, jsonify
from backend.routes.forecast_api import register_forecast_blueprint

app = Flask(__name__)

# Register forecast endpoints
register_forecast_blueprint(app)

# Now available:
# POST /api/forecast/<user_id>
# POST /api/forecast/<user_id>/scenarios
# POST /api/forecast/<user_id>/summary


# 3. EXTRACT MONTHLY BREAKDOWN
# ============================================================================

def get_monthly_breakdown(forecast_result):
    """Extract monthly savings breakdown from forecast."""
    monthly_data = forecast_result['savings_projection']['monthly_savings']
    
    for month in monthly_data:
        print(f"{month['month']}:")
        print(f"  Income:       ₹{month['income']:>10,.0f}")
        print(f"  Expenses:     ₹{month['expenses']:>10,.0f}")
        print(f"  Savings:      ₹{month['savings']:>10,.0f}")
        print(f"  Balance:      ₹{month['cumulative_balance']:>10,.0f}")
        print()


# 4. SCENARIO ANALYSIS
# ============================================================================

from backend.ml.financial_forecast import analyze_scenarios

# Get worst-case scenario when expenses increase by 20%
scenarios = analyze_scenarios(
    baseline_forecast=result,
    expense_increase_percent=20,
    income_increase_percent=0
)

print(f"Baseline savings:  ₹{scenarios['baseline_monthly_savings']:,.0f}/month")
print(f"Worst case:        ₹{scenarios['worst_case_monthly_savings']:,.0f}/month")
print(f"Best case:         ₹{scenarios['best_case_monthly_savings']:,.0f}/month")


# 5. STREAMLIT DASHBOARD
# ============================================================================

# Run interactive dashboard:
# $ streamlit run frontend/forecast_dashboard.py

# Dashboard features:
# - Real-time forecast generation
# - Interactive charts (Plotly)
# - Scenario comparison
# - Expense breakdown
# - CSV/JSON export
# - Financial recommendations


# 6. VALIDATION & ERROR HANDLING
# ============================================================================

from datetime import datetime, timedelta

def validate_transactions(expense_transactions, income_transactions):
    """Validate transaction data before forecasting."""
    
    # Check required fields
    errors = []
    
    if not expense_transactions:
        errors.append("expense_transactions: required, cannot be empty")
    
    if not income_transactions:
        errors.append("income_transactions: required, cannot be empty")
    
    # Check minimum data points
    if len(expense_transactions) < 30:
        errors.append(f"expense_transactions: minimum 30 required, got {len(expense_transactions)}")
    
    # Check data quality
    for tx in expense_transactions:
        if not all(k in tx for k in ['date', 'amount', 'type']):
            errors.append(f"expense_transactions: missing required field (date, amount, type)")
            break
        
        if tx['amount'] < 0:
            errors.append(f"expense_transactions: amounts must be positive")
            break
        
        try:
            datetime.strptime(tx['date'], '%Y-%m-%d')
        except ValueError:
            errors.append(f"expense_transactions: invalid date format (use YYYY-MM-DD)")
            break
    
    if errors:
        raise ValueError('\n'.join(errors))
    
    return True


# 7. DATABASE STORAGE
# ============================================================================

from datetime import datetime

def store_forecast(user_id, forecast_result, db):
    """Store forecast in database for historical tracking."""
    
    forecast_record = {
        'user_id': user_id,
        'forecast_data': forecast_result,
        'model': forecast_result['summary']['model_used'],
        'created_at': datetime.now().isoformat(),
        'projected_balance': forecast_result['savings_projection']['projected_balance'],
        'avg_monthly_savings': forecast_result['savings_projection']['average_monthly_savings'],
    }
    
    db.insert('forecasts', forecast_record)
    return forecast_record


# 8. COMPARE FORECAST VS ACTUAL
# ============================================================================

def compare_forecast_to_actual(user_id, db, forecast_date):
    """Compare 1-month-old forecast to actual results."""
    
    # Get forecast made a month ago
    past_forecast = db.query('forecasts').filter(
        user_id=user_id,
        created_at__gte=forecast_date - timedelta(days=2),
        created_at__lte=forecast_date + timedelta(days=2)
    ).one()
    
    if not past_forecast:
        return None
    
    # Get actual expenses for past month
    actual_transactions = db.query('transactions').filter(
        user_id=user_id,
        date__gte=forecast_date,
        date__lte=datetime.now(),
        type='expense'
    ).all()
    
    actual_total = sum(tx['amount'] for tx in actual_transactions)
    predicted_total = past_forecast['forecast_data']['predicted_expenses_next_6_months'][0]['predicted']
    
    accuracy = 100 - abs((actual_total - predicted_total) / predicted_total * 100)
    
    return {
        'predicted': predicted_total,
        'actual': actual_total,
        'accuracy': accuracy,
        'difference': actual_total - predicted_total
    }


# 9. BATCH FORECAST MULTIPLE USERS
# ============================================================================

def batch_forecast_users(user_ids, transaction_db):
    """Generate forecasts for multiple users."""
    
    results = {}
    
    for user_id in user_ids:
        try:
            # Get user's transactions
            user_transactions = transaction_db.get_user_transactions(user_id)
            
            if len(user_transactions) < 30:
                results[user_id] = {'status': 'insufficient_data'}
                continue
            
            # Split into income/expenses
            expenses = [tx for tx in user_transactions if tx['type'] == 'expense']
            income = [tx for tx in user_transactions if tx['type'] == 'income']
            
            # Generate forecast
            forecast = forecast_expenses_and_savings(
                expense_transactions=expenses,
                income_transactions=income,
                model_type='prophet',
                forecast_months=6
            )
            
            results[user_id] = {
                'status': 'success',
                'projected_balance': forecast['savings_projection']['projected_balance'],
                'avg_savings': forecast['savings_projection']['average_monthly_savings']
            }
            
        except Exception as e:
            results[user_id] = {'status': 'error', 'message': str(e)}
    
    return results


# 10. CONFIGURE FOR PRODUCTION
# ============================================================================

import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
CONFIG = {
    'MODEL': os.getenv('FORECAST_MODEL', 'prophet'),
    'FORECAST_MONTHS': int(os.getenv('FORECAST_MONTHS', '6')),
    'CONFIDENCE_LEVEL': float(os.getenv('CONFIDENCE_LEVEL', '0.95')),
    'AGGREGATION': os.getenv('AGGREGATION', 'daily'),
    'CACHE_MINUTES': int(os.getenv('CACHE_MINUTES', '60')),
    'REQUEST_TIMEOUT': int(os.getenv('REQUEST_TIMEOUT', '30')),
}

# Usage:
result = forecast_expenses_and_savings(
    expense_transactions=expenses,
    income_transactions=income,
    model_type=CONFIG['MODEL'],
    forecast_months=CONFIG['FORECAST_MONTHS'],
    aggregation=CONFIG['AGGREGATION']
)


# 11. ADD CACHING
# ============================================================================

from functools import lru_cache
import hashlib
import json

forecast_cache = {}

def get_forecast_cached(user_id, transactions):
    """Get forecast with caching."""
    
    # Create hash of transactions
    tx_hash = hashlib.md5(
        json.dumps(transactions, sort_keys=True).encode()
    ).hexdigest()
    
    cache_key = f"{user_id}_{tx_hash}"
    
    # Return from cache if available
    if cache_key in forecast_cache:
        return forecast_cache[cache_key]
    
    # Generate new forecast
    expenses = [tx for tx in transactions if tx['type'] == 'expense']
    income = [tx for tx in transactions if tx['type'] == 'income']
    
    result = forecast_expenses_and_savings(
        expense_transactions=expenses,
        income_transactions=income
    )
    
    # Cache result
    forecast_cache[cache_key] = result
    
    return result


# 12. EXPORT TO CSV
# ============================================================================

import pandas as pd

def export_forecast_to_csv(forecast_result, filename='forecast.csv'):
    """Export forecast to CSV."""
    
    monthly_data = forecast_result['savings_projection']['monthly_savings']
    df = pd.DataFrame(monthly_data)
    
    df.to_csv(filename, index=False)
    return filename


# 13. FINANCIAL HEALTH SCORE
# ============================================================================

def calculate_health_score(forecast_result):
    """Calculate overall financial health score (0-10)."""
    
    projection = forecast_result['savings_projection']
    
    # Factors
    savings_rate = (
        projection['average_monthly_savings'] / 
        (projection['average_monthly_savings'] + 
         projection['monthly_savings'][0]['expenses'])
    )
    
    trend = 1.0 if projection['savings_trend'] == 'improving' else 0.5
    balance_positive = 1.0 if projection['projected_balance'] > 0 else 0.0
    
    # Score calculation
    score = (savings_rate * 4 + trend * 3 + balance_positive * 3) * 10
    
    if score > 10:
        score = 10
    elif score < 0:
        score = 0
    
    assessment = 'Excellent' if score >= 8 else \
                 'Good' if score >= 6 else \
                 'Fair' if score >= 4 else \
                 'Poor'
    
    return {'score': round(score, 1), 'assessment': assessment}


# 14. GENERATE RECOMMENDATIONS
# ============================================================================

def generate_recommendations(forecast_result):
    """Generate actionable financial recommendations."""
    
    recommendations = []
    projection = forecast_result['savings_projection']
    expenses = projection['monthly_savings'][0]['expenses']
    income = projection['monthly_savings'][0]['income']
    savings = projection['average_monthly_savings']
    
    savings_rate = (savings / income) * 100
    
    if savings_rate > 40:
        recommendations.append("✓ Strong savings rate. Consider investing excess funds for growth.")
    elif savings_rate > 20:
        recommendations.append("✓ Healthy savings rate. Maintain current spending patterns.")
    elif savings_rate > 10:
        recommendations.append("⚠ Moderate savings. Look for opportunities to reduce discretionary spending.")
    else:
        recommendations.append("⚠ Low savings rate. Review and reduce non-essential expenses.")
    
    if projection['savings_trend'] == 'declining':
        recommendations.append("⚠ Savings trend declining. Monitor expense growth patterns.")
    
    if projection['projected_balance'] < 0:
        recommendations.append("⚠ Projected balance will be negative. Increase income or reduce expenses.")
    
    return recommendations


# 15. TEST ENDPOINTS
# ============================================================================

"""
Test forecasting endpoints:

$ curl -X POST http://localhost:5000/api/forecast/user123 \
  -H "Content-Type: application/json" \
  -d '{
    "expense_transactions": [
      {"date": "2024-01-15", "amount": 2500, "category": "groceries", "type": "expense"},
      {"date": "2024-01-16", "amount": 150, "category": "transport", "type": "expense"}
    ],
    "income_transactions": [
      {"date": "2024-01-01", "amount": 50000, "category": "salary", "type": "income"}
    ]
  }'

$ streamlit run frontend/forecast_dashboard.py

$ python backend/ml/test_financial_forecast.py
"""


# ============================================================================
# CHEAT SHEET
# ============================================================================

"""
Parameters Summary:
├── expense_transactions (required): List of {'date', 'amount', 'category', 'type'}
├── income_transactions (required): List of {'date', 'amount', 'category', 'type'}
├── model_type: 'prophet' (default) or 'arima'
├── forecast_months: 1-24 (default: 6)
├── starting_balance: Initial account balance (default: 0)
└── aggregation: 'daily' (default), 'weekly', or 'monthly'

Response Structure:
├── predicted_expenses_next_6_months: Array of monthly predictions
│   └── {date, predicted, lower_bound, upper_bound, confidence_interval}
├── savings_projection: Detailed savings breakdown
│   ├── monthly_savings: Array of {month, income, expenses, savings, cumulative_balance}
│   ├── average_monthly_savings: Float
│   ├── projected_balance: Float
│   └── savings_trend: 'improving', 'stable', or 'declining'
└── summary: Metadata
    ├── model_used: String
    ├── confidence_level: Float
    └── prediction_accuracy: String

Common Errors:
├── 400 Bad Request: Missing/invalid parameters
├── 400 Insufficient Data: < 30 transactions
├── 500 Model Error: Prophet/ARIMA not available
└── 504 Timeout: Large dataset, use monthly aggregation

Performance Tips:
├── Use monthly aggregation for 5+ years of data
├── Cache forecasts for 60 minutes
├── Use ARIMA for <100ms response requirement
└── Limit forecast_months to 12 for real-time use
"""
