# Financial Forecasting Integration Guide

Complete reference for integrating the financial forecasting module into SmartBridge.

## 📋 Table of Contents
1. [Installation](#installation)
2. [API Endpoints](#api-endpoints)
3. [Database Integration](#database-integration)
4. [Configuration](#configuration)
5. [Examples](#examples)
6. [Error Handling](#error-handling)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### 1. Install Required Dependencies

```bash
pip install prophet statsmodels pandas numpy
```

**Version Requirements:**
- Prophet >= 1.1
- statsmodels >= 0.14
- pandas >= 1.3
- numpy >= 1.21

### 2. Register Flask Blueprint

In your main Flask app (`app.py` or `main.py`):

```python
from flask import Flask
from backend.routes.forecast_api import register_forecast_blueprint

app = Flask(__name__)

# Register forecasting routes
register_forecast_blueprint(app)

if __name__ == '__main__':
    app.run(debug=True)
```

### 3. Verify Installation

```bash
python backend/ml/test_financial_forecast.py
```

Expected output:
```
🧪 FINANCIAL FORECAST MODULE TEST SUITE 🧪

Available Models:
  Prophet: ✓ Available
  ARIMA: ✓ Available

TEST 1: Data Preparation
...
✅ ALL TESTS PASSED SUCCESSFULLY!
```

---

## API Endpoints

### 1. Generate Forecast

**Endpoint:** `POST /api/forecast/{user_id}`

**Description:** Generate expense and savings forecast for a user

**Request Body:**

```json
{
  "expense_transactions": [
    {
      "date": "2024-01-15",
      "amount": 2500.50,
      "category": "groceries",
      "type": "expense"
    },
    {
      "date": "2024-01-16",
      "amount": 150.00,
      "category": "transport",
      "type": "expense"
    }
  ],
  "income_transactions": [
    {
      "date": "2024-01-01",
      "amount": 50000.00,
      "category": "salary",
      "type": "income"
    }
  ],
  "model_type": "prophet",
  "forecast_months": 6,
  "starting_balance": 10000.00,
  "aggregation": "daily"
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `expense_transactions` | Array | Required | List of expense transactions with date/amount |
| `income_transactions` | Array | Required | List of income transactions with date/amount |
| `model_type` | String | `prophet` | `prophet` or `arima` |
| `forecast_months` | Integer | `6` | Number of months to forecast (1-24) |
| `starting_balance` | Float | `0` | Starting account balance (₹) |
| `aggregation` | String | `daily` | `daily`, `weekly`, or `monthly` |

**Success Response (200):**

```json
{
  "success": true,
  "data": {
    "predicted_expenses_next_6_months": [
      {
        "date": "2024-07-01",
        "date_label": "July 2024",
        "predicted": 32000,
        "lower_bound": 28500,
        "upper_bound": 35500,
        "confidence_interval": "95%"
      },
      {
        "date": "2024-08-01",
        "date_label": "August 2024",
        "predicted": 31500,
        "lower_bound": 27800,
        "upper_bound": 35200,
        "confidence_interval": "95%"
      }
    ],
    "savings_projection": {
      "monthly_savings": [
        {
          "month": "2024-07",
          "income": 50000,
          "expenses": 32000,
          "savings": 18000,
          "cumulative_balance": 28000,
          "monthly_savings_rate": 0.36
        }
      ],
      "average_monthly_savings": 18000,
      "total_projected_savings": 108000,
      "projected_balance": 118000,
      "savings_trend": "improving",
      "savings_volatility": 0.15
    },
    "summary": {
      "model_used": "prophet",
      "confidence_level": 0.95,
      "forecast_period": "6 months",
      "prediction_accuracy": "MAPE: 12.5%",
      "data_points_used": 180
    }
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Missing required field: expense_transactions",
  "status": 400
}
```

---

### 2. Scenario Analysis

**Endpoint:** `POST /api/forecast/{user_id}/scenarios`

**Description:** Analyze forecast under different scenarios (best/worst/baseline)

**Request Body:**

```json
{
  "baseline_forecast": {
    "predicted_expenses_next_6_months": [...],
    "savings_projection": {...}
  },
  "expense_increase_percent": 10,
  "income_increase_percent": 5
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "baseline_monthly_savings": 18000,
    "best_case_monthly_savings": 20000,
    "worst_case_monthly_savings": 14000,
    "best_case_scenario": {
      "description": "Income increases by 5%, expenses stay flat",
      "monthly_savings": 20000,
      "6_month_savings": 120000
    },
    "worst_case_scenario": {
      "description": "Expenses increase by 10%, income stays flat",
      "monthly_savings": 14000,
      "6_month_savings": 84000
    },
    "impact_analysis": {
      "10% expense_increase_impact": -4000,
      "5% income_increase_impact": 2500
    }
  }
}
```

---

### 3. Forecast Summary

**Endpoint:** `POST /api/forecast/{user_id}/summary`

**Description:** Get summary statistics of forecast

**Request Body:**

```json
{
  "forecast_data": {
    "predicted_expenses_next_6_months": [...],
    "savings_projection": {...}
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "total_projected_expense": 192000,
    "average_monthly_expense": 32000,
    "total_projected_savings": 108000,
    "average_monthly_savings": 18000,
    "projected_final_balance": 118000,
    "financial_health_score": 7.8,
    "health_assessment": "Good",
    "recommendations": [
      "Your savings are strong at 36% of income",
      "Consider investing excess savings",
      "Maintain current spending patterns"
    ]
  }
}
```

---

## Database Integration

### 1. Database Models

Add to your `backend/models/forecast.py`:

```python
from datetime import datetime
from typing import List, Dict

class ForecastResult:
    """Store forecasting results for historical tracking"""
    
    def __init__(self, user_id: str, forecast_data: Dict):
        self.id = None
        self.user_id = user_id
        self.forecast_data = forecast_data
        self.model_type = forecast_data.get('summary', {}).get('model_used', 'unknown')
        self.confidence_level = forecast_data.get('summary', {}).get('confidence_level', 0.95)
        self.created_at = datetime.now()
        self.forecast_months = forecast_data.get('summary', {}).get('forecast_period', '6')
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'forecast_data': self.forecast_data,
            'model_type': self.model_type,
            'created_at': self.created_at.isoformat(),
        }

class TransactionHistory:
    """Store transaction history for forecasting"""
    
    def __init__(self, user_id: str, date: str, amount: float, 
                 transaction_type: str, category: str):
        self.user_id = user_id
        self.date = date
        self.amount = amount
        self.transaction_type = transaction_type  # 'income' or 'expense'
        self.category = category
        self.created_at = datetime.now()
```

### 2. Database Queries

Add endpoints to fetch transaction history:

```python
@app.route('/api/transactions/<user_id>', methods=['GET'])
def get_transactions(user_id):
    """Fetch user's transaction history"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date', date.today().isoformat())
    
    # Query database for transactions in date range
    transactions = db.query(TransactionHistory).filter(
        TransactionHistory.user_id == user_id,
        TransactionHistory.date >= start_date,
        TransactionHistory.date <= end_date
    ).all()
    
    return jsonify([t.to_dict() for t in transactions])

@app.route('/api/forecast/<user_id>/history', methods=['GET'])
def get_forecast_history(user_id):
    """Fetch previous forecasts for comparison"""
    forecasts = db.query(ForecastResult).filter(
        ForecastResult.user_id == user_id
    ).order_by(ForecastResult.created_at.desc()).limit(10).all()
    
    return jsonify([f.to_dict() for f in forecasts])
```

### 3. Store Forecasts

In `forecast_api.py`, add caching:

```python
@app.route('/api/forecast/<user_id>', methods=['POST'])
def generate_forecast(user_id):
    # ... existing code ...
    
    # Store forecast in database
    forecast_result = ForecastResult(user_id, result)
    db.session.add(forecast_result)
    db.session.commit()
    
    return jsonify(_format_response(result))
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Forecasting Configuration
FORECAST_DEFAULT_MODEL=prophet
FORECAST_CONFIDENCE_LEVEL=0.95
FORECAST_DEFAULT_MONTHS=6
FORECAST_AGGREGATION=daily
FORECAST_CACHE_ENABLED=true
FORECAST_CACHE_MINUTES=60

# Model Parameters
PROPHET_SEASONALITY_MODE=additive
ARIMA_ORDER=1,1,1
ARIMA_SEASONAL_ORDER=1,1,1,12

# Performance
FORECAST_BATCH_SIZE=100
FORECAST_TIMEOUT_SECONDS=30
```

### Load Configuration

In `forecast_api.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = os.getenv('FORECAST_DEFAULT_MODEL', 'prophet')
CONFIDENCE_LEVEL = float(os.getenv('FORECAST_CONFIDENCE_LEVEL', '0.95'))
DEFAULT_MONTHS = int(os.getenv('FORECAST_DEFAULT_MONTHS', '6'))
CACHE_ENABLED = os.getenv('FORECAST_CACHE_ENABLED', 'true').lower() == 'true'
```

---

## Examples

### Example 1: Basic Forecast

**cURL:**

```bash
curl -X POST http://localhost:5000/api/forecast/user123 \
  -H "Content-Type: application/json" \
  -d '{
    "expense_transactions": [
      {"date": "2024-01-15", "amount": 2500, "category": "groceries", "type": "expense"},
      {"date": "2024-01-16", "amount": 150, "category": "transport", "type": "expense"},
      {"date": "2024-01-17", "amount": 500, "category": "entertainment", "type": "expense"}
    ],
    "income_transactions": [
      {"date": "2024-01-01", "amount": 50000, "category": "salary", "type": "income"}
    ],
    "model_type": "prophet",
    "forecast_months": 6
  }'
```

**Python:**

```python
import requests
import json

url = "http://localhost:5000/api/forecast/user123"

payload = {
    "expense_transactions": [
        {"date": "2024-01-15", "amount": 2500, "category": "groceries", "type": "expense"},
        {"date": "2024-01-16", "amount": 150, "category": "transport", "type": "expense"},
        {"date": "2024-01-17", "amount": 500, "category": "entertainment", "type": "expense"}
    ],
    "income_transactions": [
        {"date": "2024-01-01", "amount": 50000, "category": "salary", "type": "income"}
    ],
    "model_type": "prophet",
    "forecast_months": 6
}

response = requests.post(url, json=payload)
result = response.json()

if result['success']:
    forecast = result['data']
    print(f"6-Month Projection: ₹{forecast['savings_projection']['projected_balance']:,.0f}")
else:
    print(f"Error: {result['error']}")
```

### Example 2: Scenario Analysis

```python
# After getting baseline forecast
scenarios_payload = {
    "baseline_forecast": result['data'],
    "expense_increase_percent": 15,
    "income_increase_percent": 0
}

response = requests.post(
    f"http://localhost:5000/api/forecast/user123/scenarios",
    json=scenarios_payload
)

scenarios = response.json()['data']
print(f"Worst case savings: ₹{scenarios['worst_case_monthly_savings']:,.0f}/month")
```

### Example 3: Streamlit Dashboard

```bash
streamlit run frontend/forecast_dashboard.py
```

Runs the interactive forecast dashboard with:
- Real-time forecast generation
- Multiple visualization types
- Scenario comparison
- CSV/JSON export

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `400: Missing required field` | Missing parameter | Check request body for all required fields |
| `400: Invalid model type` | Model not available | Install Prophet/ARIMA: `pip install prophet statsmodels` |
| `400: Insufficient data` | < 30 days of history | Provide at least 30 days of transactions |
| `500: Forecast generation failed` | Data quality issue | Check transaction amounts are positive numbers |
| `504: Request timeout` | processing too long | Use monthly aggregation for large datasets |

### Error Response Format

```json
{
  "success": false,
  "error": "Insufficient data for forecasting. Minimum 30 transactions required.",
  "status": 400,
  "details": {
    "transactions_provided": 15,
    "transactions_required": 30,
    "suggestion": "Please provide at least one month of historical data"
  }
}
```

### Implement Error Handling

```python
from flask import jsonify

try:
    forecast = forecast_expenses_and_savings(...)
    return jsonify({'success': True, 'data': forecast}), 200
except ValueError as e:
    return jsonify({
        'success': False,
        'error': str(e),
        'status': 400
    }), 400
except Exception as e:
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'status': 500,
        'details': str(e) if DEBUG else None
    }), 500
```

---

## Performance Tuning

### 1. Use Monthly Aggregation for Large Datasets

```python
# For 5+ years of transactions
result = forecast_expenses_and_savings(
    expense_transactions=transactions,
    income_transactions=income,
    aggregation='monthly'  # Instead of 'daily'
)
```

Performance improvement: 10x faster with monthly aggregation

### 2. Cache Forecasts

```python
from functools import lru_cache
from datetime import datetime, timedelta

forecast_cache = {}
cache_expiry = 60  # minutes

def get_forecast_cached(user_id, transactions_hash):
    if user_id in forecast_cache:
        cached = forecast_cache[user_id]
        if datetime.now() - cached['time'] < timedelta(minutes=cache_expiry):
            return cached['data']
    
    # Generate new forecast
    result = forecast_expenses_and_savings(...)
    forecast_cache[user_id] = {
        'data': result,
        'time': datetime.now()
    }
    return result
```

### 3. Use ARIMA for Speed

Prophet is more accurate but slower. Use ARIMA for real-time requests:

```python
# For <100ms response time requirement
result = forecast_expenses_and_savings(
    expense_transactions=transactions,
    income_transactions=income,
    model_type='arima',  # Faster than Prophet
    aggregation='monthly'
)
```

---

## Troubleshooting

### Prophet Not Available

```python
ImportError: No module named 'prophet'
```

**Solution:**
```bash
pip install prophet --no-cache-dir
# If still failing:
conda install -c conda-forge prophet
```

### ARIMA Not Available

```python
ImportError: No module named 'statsmodels'
```

**Solution:**
```bash
pip install statsmodels
```

### Forecast Accuracy Low

If MAPE > 30%, try:
1. Increase training data (more historical transactions)
2. Use different aggregation (`monthly` instead of `daily`)
3. Switch models: `model_type='arima'` or `model_type='prophet'`
4. Check for data outliers/anomalies

### Process Timeout

```
RuntimeError: Forecast generation exceeded timeout
```

**Solution:**
1. Use monthly aggregation: `aggregation='monthly'`
2. Reduce forecast period: `forecast_months=3`
3. Use ARIMA model: `model_type='arima'`
4. Increase server timeout in Flask: `PROPAGATE_EXCEPTIONS=True`

---

## Quick Reference

### API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/forecast/{user_id}` | POST | Generate forecast |
| `/api/forecast/{user_id}/scenarios` | POST | Scenario analysis |
| `/api/forecast/{user_id}/summary` | POST | Summary statistics |
| `/api/transactions/{user_id}` | GET | Fetch transaction history |
| `/api/forecast/{user_id}/history` | GET | Forecast history |

### Key Functions

```python
from backend.ml.financial_forecast import forecast_expenses_and_savings

result = forecast_expenses_and_savings(
    expense_transactions=[...],
    income_transactions=[...],
    model_type='prophet',
    forecast_months=6,
    starting_balance=10000
)
# Returns: {'predicted_expenses_next_6_months': [...], 'savings_projection': {...}, ...}
```

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Run test suite: `python backend/ml/test_financial_forecast.py`
3. Review API response errors for detailed messages
4. Check logs: Enable DEBUG mode to see full error traces

---

Last Updated: 2024
Platform: SmartBridge Financial System
