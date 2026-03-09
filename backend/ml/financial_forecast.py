"""Machine Learning Financial Forecasting Module.

Predicts future expenses and savings using time series analysis.
Supports Prophet and ARIMA models for forecasting.

Features:
- Historical transaction analysis
- Future expense prediction (6 months)
- Savings projection
- Trend detection
- Seasonality analysis
- Confidence intervals

Models Supported:
- Prophet (Facebook) - Better for seasonal data
- ARIMA - Classical time series
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta, date
import numpy as np
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
import warnings
import logging

# Configure logging
logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')

# Try to import Prophet, fall back to ARIMA
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from statsmodels.tsa.arima.model import ARIMA
    ARIMA_AVAILABLE = True
except ImportError:
    ARIMA_AVAILABLE = False
    logger.warning("ARIMA not available. Install statsmodels: pip install statsmodels")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available. Install: pip install prophet")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _round_currency(value: float) -> float:
    """Round monetary value to 2 decimal places."""
    if not isinstance(value, (int, float)):
        return value
    d = Decimal(str(float(value)))
    return float(d.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _ensure_dataframe(data: Any) -> pd.DataFrame:
    """Ensure input is a pandas DataFrame."""
    if isinstance(data, pd.DataFrame):
        return data
    elif isinstance(data, dict):
        return pd.DataFrame(data)
    elif isinstance(data, list):
        return pd.DataFrame(data)
    else:
        raise TypeError(f"Cannot convert {type(data)} to DataFrame")


# ============================================================================
# DATA PREPARATION
# ============================================================================

def prepare_transaction_data(
    transactions: List[Dict[str, Any]],
    aggregation: str = 'daily',
) -> pd.DataFrame:
    """Prepare transaction data for forecasting.
    
    Args:
        transactions: List of transaction dicts with 'date', 'amount', 'type'
        aggregation: 'daily', 'weekly', or 'monthly' aggregation
        
    Returns:
        DataFrame with ds (date) and y (amount) columns for forecasting
        
    Example:
        transactions = [
            {'date': '2024-01-01', 'amount': 1000, 'type': 'expense'},
            {'date': '2024-01-02', 'amount': 500, 'type': 'expense'},
        ]
        df = prepare_transaction_data(transactions, aggregation='daily')
    """
    
    df = pd.DataFrame(transactions)
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        raise ValueError("Transactions must have 'date' column")
    
    # Ensure amount column exists
    if 'amount' not in df.columns:
        raise ValueError("Transactions must have 'amount' column")
    
    # Convert amount to float
    df['amount'] = df['amount'].astype(float).abs()
    
    # Aggregate by date
    if aggregation == 'daily':
        df_agg = df.groupby('date')['amount'].sum().reset_index()
        df_agg['date'] = pd.to_datetime(df_agg['date']).dt.normalize()
    elif aggregation == 'weekly':
        df['week'] = df['date'].dt.to_period('W')
        df_agg = df.groupby('week')['amount'].sum().reset_index()
        df_agg['date'] = df_agg['week'].dt.to_timestamp()
    elif aggregation == 'monthly':
        df['month'] = df['date'].dt.to_period('M')
        df_agg = df.groupby('month')['amount'].sum().reset_index()
        df_agg['date'] = df_agg['month'].dt.to_timestamp()
    else:
        raise ValueError("aggregation must be 'daily', 'weekly', or 'monthly'")
    
    # Prepare for forecasting (Prophet format: ds, y)
    df_prepared = pd.DataFrame({
        'ds': df_agg['date'],
        'y': df_agg['amount']
    })
    
    # Sort by date
    df_prepared = df_prepared.sort_values('ds').reset_index(drop=True)
    
    # Fill missing dates with 0 (no transactions)
    date_range = pd.date_range(
        start=df_prepared['ds'].min(),
        end=df_prepared['ds'].max(),
        freq='D'
    )
    df_prepared = df_prepared.set_index('ds').reindex(date_range, fill_value=0).reset_index()
    df_prepared.columns = ['ds', 'y']
    
    return df_prepared


# ============================================================================
# FORECAST MODELS
# ============================================================================

def forecast_with_prophet(
    df: pd.DataFrame,
    periods: int = 180,  # 6 months
    interval_width: float = 0.95,
    seasonality_mode: str = 'additive',
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Forecast using Facebook Prophet.
    
    Args:
        df: DataFrame with 'ds' (date) and 'y' (value) columns
        periods: Number of periods to forecast (default: 180 days)
        interval_width: Confidence interval width (default: 0.95 = 95%)
        seasonality_mode: 'additive' or 'multiplicative'
        
    Returns:
        Tuple of (forecast_df, model_info)
        
    Example:
        forecast_df, info = forecast_with_prophet(df, periods=180)
        print(forecast_df[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])
    """
    
    if not PROPHET_AVAILABLE:
        raise ImportError("Prophet not available. Install: pip install prophet")
    
    if len(df) < 30:
        raise ValueError("Need at least 30 data points for Prophet forecasting")
    
    try:
        # Initialize Prophet
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=interval_width,
            seasonality_mode=seasonality_mode,
        )
        
        # Fit the model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model.fit(df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=periods)
        
        # Make forecast
        forecast = model.predict(future)
        
        # Extract relevant columns
        forecast_result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        forecast_result.columns = ['date', 'predicted', 'lower_bound', 'upper_bound']
        
        # Model info
        model_info = {
            'model': 'Prophet',
            'periods_trained': len(df),
            'periods_forecasted': periods,
            'seasonality_mode': seasonality_mode,
            'interval_width': interval_width,
            'mape': calculate_mape(df['y'].values, forecast[:len(df)]['yhat'].values),
        }
        
        return forecast_result, model_info
        
    except Exception as e:
        logger.error(f"Prophet forecasting failed: {str(e)}")
        raise


def forecast_with_arima(
    df: pd.DataFrame,
    periods: int = 180,
    order: Tuple[int, int, int] = (1, 1, 1),
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Forecast using ARIMA.
    
    Args:
        df: DataFrame with 'ds' and 'y' columns
        periods: Number of periods to forecast (default: 180)
        order: ARIMA order (p, d, q) tuple. Default: (1, 1, 1)
        
    Returns:
        Tuple of (forecast_df, model_info)
        
    Example:
        forecast_df, info = forecast_with_arima(df, periods=180)
    """
    
    if not ARIMA_AVAILABLE:
        raise ImportError("ARIMA not available. Install: pip install statsmodels")
    
    if len(df) < 20:
        raise ValueError("Need at least 20 data points for ARIMA forecasting")
    
    try:
        # Fit ARIMA model
        model = ARIMA(df['y'], order=order)
        fitted_model = model.fit()
        
        # Make forecast with confidence intervals
        forecast_result = fitted_model.get_forecast(steps=periods)
        forecast_df = forecast_result.conf_int(alpha=0.05)
        forecast_df.columns = ['lower_bound', 'upper_bound']
        forecast_df['predicted'] = forecast_result.predicted_mean
        
        # Add dates
        last_date = df['ds'].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=periods,
            freq='D'
        )
        forecast_df['date'] = future_dates
        forecast_df = forecast_df[['date', 'predicted', 'lower_bound', 'upper_bound']]
        forecast_df = forecast_df.reset_index(drop=True)
        
        # Model info
        model_info = {
            'model': 'ARIMA',
            'order': order,
            'periods_trained': len(df),
            'periods_forecasted': periods,
            'aic': fitted_model.aic,
            'bic': fitted_model.bic,
        }
        
        return forecast_df, model_info
        
    except Exception as e:
        logger.error(f"ARIMA forecasting failed: {str(e)}")
        raise


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error."""
    mask = y_true != 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


# ============================================================================
# FORECAST AGGREGATION & PROCESSING
# ============================================================================

def aggregate_forecast_to_monthly(
    forecast_df: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate daily forecast to monthly values.
    
    Args:
        forecast_df: Daily forecast DataFrame
        
    Returns:
        Monthly aggregated forecast
    """
    
    forecast_df = forecast_df.copy()
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])
    forecast_df['month'] = forecast_df['date'].dt.to_period('M')
    
    # Aggregate predictions
    monthly = forecast_df.groupby('month').agg({
        'predicted': 'sum',
        'lower_bound': 'sum',
        'upper_bound': 'sum',
    }).reset_index()
    
    monthly['date'] = monthly['month'].dt.to_timestamp()
    return monthly[['date', 'predicted', 'lower_bound', 'upper_bound']]


# ============================================================================
# SAVINGS PROJECTION
# ============================================================================

def project_savings(
    income_data: List[Dict[str, Any]],
    expenses_forecast: pd.DataFrame,
    months: int = 6,
    starting_balance: float = 0,
) -> Dict[str, Any]:
    """Project future savings based on income and expense forecast.
    
    Args:
        income_data: Historical income transactions
        expenses_forecast: Forecasted expenses DataFrame
        months: Number of months to project (default: 6)
        starting_balance: Starting account balance
        
    Returns:
        {
            'monthly_savings': [{month, predicted_savings}, ...],
            'cumulative_savings': [{month, total_savings}, ...],
            'average_monthly_savings': float,
            'projected_balance': float,
            'savings_trend': str
        }
    """
    
    # Calculate average monthly income
    income_df = pd.DataFrame(income_data)
    income_df['date'] = pd.to_datetime(income_df['date'])
    income_df['month'] = income_df['date'].dt.to_period('M')
    
    monthly_income = income_df.groupby('month')['amount'].sum().mean()
    
    # Aggregate expenses to monthly
    expenses_monthly = aggregate_forecast_to_monthly(expenses_forecast)
    
    # Calculate savings
    savings_data = []
    cumulative_balance = starting_balance
    
    for idx, row in expenses_monthly.head(months).iterrows():
        month = row['date']
        expenses = row['predicted']
        savings = monthly_income - expenses
        cumulative_balance += savings
        
        savings_data.append({
            'month': month.strftime('%Y-%m'),
            'income': _round_currency(monthly_income),
            'expenses': _round_currency(expenses),
            'savings': _round_currency(savings),
            'cumulative_balance': _round_currency(cumulative_balance),
        })
    
    # Calculate statistics
    total_savings = sum(s['savings'] for s in savings_data)
    avg_monthly_savings = total_savings / len(savings_data) if savings_data else 0
    
    # Determine trend
    if len(savings_data) > 1:
        first_half_avg = sum(s['savings'] for s in savings_data[:len(savings_data)//2])
        second_half_avg = sum(s['savings'] for s in savings_data[len(savings_data)//2:])
        
        if second_half_avg > first_half_avg:
            trend = "improving"
        elif second_half_avg < first_half_avg:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    return {
        'monthly_savings': savings_data,
        'average_monthly_savings': _round_currency(avg_monthly_savings),
        'total_projected_savings': _round_currency(total_savings),
        'projected_balance': _round_currency(cumulative_balance),
        'savings_trend': trend,
        'months_projected': months,
    }


# ============================================================================
# MAIN FORECASTING API
# ============================================================================

def forecast_expenses_and_savings(
    expense_transactions: List[Dict[str, Any]],
    income_transactions: List[Dict[str, Any]],
    model_type: str = 'prophet',
    forecast_months: int = 6,
    starting_balance: float = 0,
    aggregation: str = 'daily',
) -> Dict[str, Any]:
    """Generate comprehensive financial forecast.
    
    Args:
        expense_transactions: List of historical expense transactions
        income_transactions: List of historical income transactions
        model_type: 'prophet' or 'arima'
        forecast_months: Months to forecast (default: 6)
        starting_balance: Starting account balance
        aggregation: 'daily', 'weekly', or 'monthly'
        
    Returns:
        {
            'predicted_expenses_next_6_months': [
                {'date': '2024-07-01', 'predicted': 5000, 'lower_bound': 4500, 'upper_bound': 5500},
                ...
            ],
            'savings_projection': {
                'monthly_savings': [...],
                'average_monthly_savings': 3000,
                'projected_balance': 25000,
                'savings_trend': 'improving'
            },
            'model_info': {...},
            'summary': {...}
        }
        
    Example:
        result = forecast_expenses_and_savings(
            expense_transactions=expenses,
            income_transactions=income,
            model_type='prophet',
            forecast_months=6
        )
        
        for month in result['predicted_expenses_next_6_months']:
            print(f"{month['date']}: ₹{month['predicted']:,.0f}")
    """
    
    # Validate inputs
    if not expense_transactions:
        raise ValueError("No expense transactions provided")
    
    if not income_transactions:
        raise ValueError("No income transactions provided")
    
    if model_type not in ['prophet', 'arima']:
        raise ValueError("model_type must be 'prophet' or 'arima'")
    
    # Prepare data
    expense_df = prepare_transaction_data(expense_transactions, aggregation=aggregation)
    
    # Determine forecast periods
    if aggregation == 'daily':
        forecast_periods = forecast_months * 30
    elif aggregation == 'weekly':
        forecast_periods = forecast_months * 4
    elif aggregation == 'monthly':
        forecast_periods = forecast_months
    else:
        forecast_periods = forecast_months * 30
    
    # Generate forecast
    try:
        if model_type == 'prophet' and PROPHET_AVAILABLE:
            forecast_df, model_info = forecast_with_prophet(
                expense_df,
                periods=forecast_periods,
                interval_width=0.95,
            )
        elif model_type == 'arima' and ARIMA_AVAILABLE:
            forecast_df, model_info = forecast_with_arima(
                expense_df,
                periods=forecast_periods,
            )
        else:
            raise ImportError(f"{model_type} is not available")
            
    except Exception as e:
        logger.error(f"Forecasting failed: {str(e)}")
        raise
    
    # Filter to requested months
    forecast_df['date'] = pd.to_datetime(forecast_df['date'])
    cutoff_date = forecast_df['date'].max()
    forecast_months_df = forecast_df[
        forecast_df['date'] >= (datetime.utcnow().date().replace(day=1))
    ].head(forecast_periods if aggregation == 'daily' else forecast_months)
    
    # Aggregate if needed
    if aggregation == 'daily':
        forecast_months_df = aggregate_forecast_to_monthly(forecast_months_df)
    
    # Ensure positive values
    forecast_months_df['predicted'] = forecast_months_df['predicted'].clip(lower=0)
    forecast_months_df['lower_bound'] = forecast_months_df['lower_bound'].clip(lower=0)
    forecast_months_df['upper_bound'] = forecast_months_df['upper_bound'].clip(lower=0)
    
    # Round currency values
    for col in ['predicted', 'lower_bound', 'upper_bound']:
        forecast_months_df[col] = forecast_months_df[col].apply(_round_currency)
    
    # Format for output
    expenses_forecast = [
        {
            'date': row['date'].strftime('%Y-%m'),
            'predicted': row['predicted'],
            'lower_bound': row['lower_bound'],
            'upper_bound': row['upper_bound'],
        }
        for _, row in forecast_months_df.iterrows()
    ]
    
    # Project savings
    savings_projection = project_savings(
        income_transactions,
        forecast_months_df,
        months=forecast_months,
        starting_balance=starting_balance,
    )
    
    # Calculate summary statistics
    avg_predicted_expense = np.mean([e['predicted'] for e in expenses_forecast])
    total_predicted_expense = sum(e['predicted'] for e in expenses_forecast)
    
    summary = {
        'forecast_period': f"{forecast_months} months",
        'total_predicted_expenses': _round_currency(total_predicted_expense),
        'average_monthly_expenses': _round_currency(avg_predicted_expense),
        'model_used': model_info['model'],
        'data_points_used': len(expense_df),
        'confidence_interval': '95%',
    }
    
    return {
        'predicted_expenses_next_6_months': expenses_forecast,
        'savings_projection': savings_projection,
        'model_info': model_info,
        'summary': summary,
    }


# ============================================================================
# SCENARIO ANALYSIS
# ============================================================================

def analyze_scenarios(
    baseline_forecast: Dict[str, Any],
    expense_increase_percent: float = 10,
    income_increase_percent: float = 5,
) -> Dict[str, Any]:
    """Analyze different financial scenarios.
    
    Args:
        baseline_forecast: Result from forecast_expenses_and_savings()
        expense_increase_percent: Expense increase scenario (%)
        income_increase_percent: Income increase scenario (%)
        
    Returns:
        {
            'baseline': {...},
            'high_expenses_scenario': {...},
            'optimistic_scenario': {...}
        }
    """
    
    scenarios = {
        'baseline': baseline_forecast['savings_projection']['average_monthly_savings'],
    }
    
    # High expenses scenario
    high_expense_savings = (
        baseline_forecast['savings_projection']['average_monthly_savings'] -
        (np.mean([e['predicted'] for e in baseline_forecast['predicted_expenses_next_6_months']]) *
         expense_increase_percent / 100)
    )
    scenarios['high_expenses_scenario'] = _round_currency(high_expense_savings)
    
    # Optimistic scenario
    optimistic_savings = (
        baseline_forecast['savings_projection']['average_monthly_savings'] +
        (np.mean([e['predicted'] for e in baseline_forecast['predicted_expenses_next_6_months']]) *
         income_increase_percent / 100)
    )
    scenarios['optimistic_scenario'] = _round_currency(optimistic_savings)
    
    return {
        'scenarios': scenarios,
        'baseline_monthly_savings': _round_currency(baseline_forecast['savings_projection']['average_monthly_savings']),
        'best_case_monthly_savings': _round_currency(scenarios['optimistic_scenario']),
        'worst_case_monthly_savings': _round_currency(scenarios['high_expenses_scenario']),
    }
