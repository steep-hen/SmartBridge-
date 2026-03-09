"""Financial Forecasting API Endpoint.

Provides REST API for generating financial forecasts.

Endpoints:
- POST /api/forecast/{user_id} - Generate forecast for user
- GET /api/forecast/{user_id}/history - Get forecast history
- POST /api/forecast/{user_id}/scenarios - Analyze scenarios
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from typing import Dict, Any, Optional
import logging
from decimal import Decimal, ROUND_HALF_UP

# Import forecasting functions
try:
    from ml.financial_forecast import (
        forecast_expenses_and_savings,
        analyze_scenarios,
        prepare_transaction_data,
    )
    FORECAST_AVAILABLE = True
except ImportError:
    FORECAST_AVAILABLE = False
    logging.warning("Financial forecast module not available")

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
forecast_bp = Blueprint('forecast', __name__, url_prefix='/api/forecast')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _format_response(
    success: bool,
    data: Dict[str, Any] = None,
    message: str = None,
    error: str = None,
) -> Dict[str, Any]:
    """Format API response."""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if data:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
    
    return response


def _parse_date(date_string: str) -> Optional[date]:
    """Parse date string in YYYY-MM-DD format."""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


# ============================================================================
# FORECAST ENDPOINTS
# ============================================================================

@forecast_bp.route('/<user_id>', methods=['POST'])
def generate_forecast(user_id: str):
    """Generate financial forecast for a user.
    
    Request Body (JSON):
    {
        "expense_transactions": [
            {"date": "2024-01-01", "amount": 1000, "type": "expense"},
            ...
        ],
        "income_transactions": [
            {"date": "2024-01-01", "amount": 5000, "type": "income"},
            ...
        ],
        "model_type": "prophet",  # or "arima"
        "forecast_months": 6,
        "starting_balance": 10000,
        "aggregation": "daily"  # or "weekly", "monthly"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "predicted_expenses_next_6_months": [
                {"date": "2024-07", "predicted": 5000, "lower_bound": 4500, "upper_bound": 5500},
                ...
            ],
            "savings_projection": {
                "monthly_savings": [...],
                "average_monthly_savings": 3000,
                "projected_balance": 25000,
                "savings_trend": "improving"
            },
            "summary": {...}
        }
    }
    """
    
    if not FORECAST_AVAILABLE:
        return jsonify(_format_response(
            success=False,
            error='Forecast module not available. Install: pip install prophet statsmodels'
        )), 503
    
    try:
        # Get request body
        request_data = request.get_json()
        
        if not request_data:
            return jsonify(_format_response(
                success=False,
                error='Empty request body'
            )), 400
        
        # Extract parameters
        expense_transactions = request_data.get('expense_transactions', [])
        income_transactions = request_data.get('income_transactions', [])
        model_type = request_data.get('model_type', 'prophet').lower()
        forecast_months = request_data.get('forecast_months', 6)
        starting_balance = request_data.get('starting_balance', 0)
        aggregation = request_data.get('aggregation', 'daily').lower()
        
        # Validate required parameters
        if not expense_transactions:
            return jsonify(_format_response(
                success=False,
                error='Missing required parameter: expense_transactions'
            )), 400
        
        if not income_transactions:
            return jsonify(_format_response(
                success=False,
                error='Missing required parameter: income_transactions'
            )), 400
        
        # Validate model type
        if model_type not in ['prophet', 'arima']:
            return jsonify(_format_response(
                success=False,
                error='model_type must be "prophet" or "arima"'
            )), 400
        
        # Validate aggregation
        if aggregation not in ['daily', 'weekly', 'monthly']:
            return jsonify(_format_response(
                success=False,
                error='aggregation must be "daily", "weekly", or "monthly"'
            )), 400
        
        # Validate forecast months
        if not isinstance(forecast_months, int) or forecast_months < 1 or forecast_months > 24:
            return jsonify(_format_response(
                success=False,
                error='forecast_months must be integer between 1-24'
            )), 400
        
        # Generate forecast
        logger.info(f"Generating {model_type} forecast for user {user_id}")
        forecast_result = forecast_expenses_and_savings(
            expense_transactions=expense_transactions,
            income_transactions=income_transactions,
            model_type=model_type,
            forecast_months=forecast_months,
            starting_balance=starting_balance,
            aggregation=aggregation,
        )
        
        return jsonify(_format_response(
            success=True,
            data=forecast_result,
            message=f'{model_type.capitalize()} forecast generated successfully'
        )), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=f'Validation error: {str(e)}'
        )), 400
        
    except Exception as e:
        logger.error(f"Forecast generation failed: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


@forecast_bp.route('/<user_id>/scenarios', methods=['POST'])
def analyze_forecast_scenarios(user_id: str):
    """Analyze different financial scenarios based on forecast.
    
    Request Body (JSON):
    {
        "baseline_forecast": {...},  # Result from generate_forecast
        "expense_increase_percent": 10,
        "income_increase_percent": 5
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "scenarios": {
                "baseline": 3000,
                "high_expenses_scenario": 2000,
                "optimistic_scenario": 3500
            },
            "summary": {...}
        }
    }
    """
    
    if not FORECAST_AVAILABLE:
        return jsonify(_format_response(
            success=False,
            error='Forecast module not available'
        )), 503
    
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify(_format_response(
                success=False,
                error='Empty request body'
            )), 400
        
        baseline_forecast = request_data.get('baseline_forecast')
        expense_increase = request_data.get('expense_increase_percent', 10)
        income_increase = request_data.get('income_increase_percent', 5)
        
        if not baseline_forecast:
            return jsonify(_format_response(
                success=False,
                error='Missing required parameter: baseline_forecast'
            )), 400
        
        # Analyze scenarios
        scenario_results = analyze_scenarios(
            baseline_forecast=baseline_forecast,
            expense_increase_percent=expense_increase,
            income_increase_percent=income_increase,
        )
        
        return jsonify(_format_response(
            success=True,
            data=scenario_results,
            message='Scenario analysis completed successfully'
        )), 200
        
    except Exception as e:
        logger.error(f"Scenario analysis failed: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


@forecast_bp.route('/<user_id>/summary', methods=['POST'])
def get_forecast_summary(user_id: str):
    """Get a summary of the forecast.
    
    Request Body (JSON):
    {
        "forecast_data": {...}  # Result from generate_forecast
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "total_predicted_expenses": 30000,
            "average_monthly_expenses": 5000,
            "projected_savings": 18000,
            "savings_per_month": 3000,
            "financial_health": "good"
        }
    }
    """
    
    try:
        request_data = request.get_json()
        
        if not request_data:
            return jsonify(_format_response(
                success=False,
                error='Empty request body'
            )), 400
        
        forecast_data = request_data.get('forecast_data')
        
        if not forecast_data:
            return jsonify(_format_response(
                success=False,
                error='Missing required parameter: forecast_data'
            )), 400
        
        # Extract summary data
        total_expenses = forecast_data['summary']['total_predicted_expenses']
        avg_expenses = forecast_data['summary']['average_monthly_expenses']
        avg_savings = forecast_data['savings_projection']['average_monthly_savings']
        projected_balance = forecast_data['savings_projection']['projected_balance']
        savings_trend = forecast_data['savings_projection']['savings_trend']
        
        # Determine financial health
        if avg_savings > avg_expenses:
            health = "excellent"
        elif avg_savings > avg_expenses * 0.5:
            health = "good"
        elif avg_savings > 0:
            health = "fair"
        else:
            health = "poor"
        
        summary = {
            'total_predicted_expenses': total_expenses,
            'average_monthly_expenses': avg_expenses,
            'average_monthly_savings': avg_savings,
            'projected_total_balance': projected_balance,
            'savings_trend': savings_trend,
            'financial_health_score': health,
            'expense_to_income_ratio': round((avg_expenses / (avg_expenses + avg_savings)) * 100, 2)
            if (avg_expenses + avg_savings) > 0 else 0,
        }
        
        return jsonify(_format_response(
            success=True,
            data=summary,
            message='Forecast summary generated successfully'
        )), 200
        
    except Exception as e:
        logger.error(f"Summary generation failed: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@forecast_bp.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request."""
    return jsonify(_format_response(
        success=False,
        error='Bad request'
    )), 400


@forecast_bp.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found."""
    return jsonify(_format_response(
        success=False,
        error='Resource not found'
    )), 404


@forecast_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify(_format_response(
        success=False,
        error='Internal server error'
    )), 500


# ============================================================================
# MODULE REGISTRATION
# ============================================================================

def register_forecast_blueprint(app):
    """Register the forecast blueprint with Flask app.
    
    Usage:
        from routes.forecast_api import register_forecast_blueprint
        register_forecast_blueprint(app)
    """
    app.register_blueprint(forecast_bp)
    logger.info("Forecast API blueprint registered successfully")
