"""Goal Progress Tracking API Endpoints.

Provides REST API endpoints for:
- Getting goal progress metrics
- Calculating time remaining to goal completion
- Retrieving comprehensive goal analysis
- Getting dashboard highlights across all goals
- Updating goal progress

Example Usage:
    GET /api/goals/<goal_id>/progress
    GET /api/goals/<goal_id>/time-remaining
    GET /api/goals/highlights
    POST /api/goals/<goal_id>/update-progress
"""

from flask import Blueprint, request, jsonify
from datetime import date, datetime
from typing import Dict, Any, Optional
import logging

# Import progress tracker functions
from finance.progress_tracker import (
    calculate_goal_progress,
    calculate_time_remaining,
    get_goal_progress_analysis,
    calculate_goal_highlights,
)

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
goals_bp = Blueprint('goals', __name__, url_prefix='/api/goals')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _parse_date(date_string: str) -> Optional[date]:
    """Parse date string in YYYY-MM-DD format.
    
    Args:
        date_string: Date as string
        
    Returns:
        date object or None if invalid
    """
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _format_response(
    success: bool,
    data: Dict[str, Any] = None,
    message: str = None,
    error: str = None,
) -> Dict[str, Any]:
    """Format API response.
    
    Args:
        success: Whether request was successful
        data: Response data
        message: Success message
        error: Error message
        
    Returns:
        Formatted response dict
    """
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


# ============================================================================
# GOAL PROGRESS ENDPOINTS
# ============================================================================

@goals_bp.route('/<goal_id>/progress', methods=['GET'])
def get_goal_progress_endpoint(goal_id: str):
    """Get progress percentage for a goal.
    
    Query Parameters:
        - target_amount: Target goal amount (required)
        - current_amount: Current savings (required)
        
    Returns:
        {
            "success": true,
            "data": {
                "goal_id": str,
                "goal_progress_percent": float,
                "remaining_amount": float,
                "progress_status": str
            }
        }
        
    Example:
        GET /api/goals/goal-123/progress?target_amount=500000&current_amount=250000
    """
    try:
        # Get query parameters
        target_amount = request.args.get('target_amount', type=float)
        current_amount = request.args.get('current_amount', type=float, default=0)
        
        # Validate required parameters
        if target_amount is None:
            return jsonify(_format_response(
                success=False,
                error='Missing required parameter: target_amount'
            )), 400
        
        # Calculate progress
        progress = calculate_goal_progress(target_amount, current_amount)
        
        # Add goal_id to response
        progress['goal_id'] = goal_id
        
        return jsonify(_format_response(
            success=True,
            data=progress,
            message='Goal progress calculated successfully'
        )), 200
        
    except Exception as e:
        logger.error(f"Error calculating goal progress: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


@goals_bp.route('/<goal_id>/time-remaining', methods=['GET'])
def get_time_remaining_endpoint(goal_id: str):
    """Calculate time remaining to complete goal.
    
    Query Parameters:
        - target_amount: Target amount (required)
        - current_amount: Current savings (required)
        - monthly_contribution: Monthly contribution (required)
        - target_date: Target date in YYYY-MM-DD format (optional)
        - annual_return: Expected annual return (default: 0.06 = 6%)
        
    Returns:
        {
            "success": true,
            "data": {
                "goal_id": str,
                "months_remaining": int,
                "years_remaining": float,
                "expected_completion_date": str,
                "on_track": bool,
                "feasible": bool,
                "message": str
            }
        }
        
    Example:
        GET /api/goals/goal-123/time-remaining?target_amount=500000&current_amount=250000&monthly_contribution=5000&target_date=2026-12-31
    """
    try:
        # Get query parameters
        target_amount = request.args.get('target_amount', type=float)
        current_amount = request.args.get('current_amount', type=float, default=0)
        monthly_contribution = request.args.get('monthly_contribution', type=float)
        target_date_str = request.args.get('target_date')
        annual_return = request.args.get('annual_return', type=float, default=0.06)
        
        # Validate required parameters
        if not all([target_amount, monthly_contribution is not None]):
            return jsonify(_format_response(
                success=False,
                error='Missing required parameters: target_amount, monthly_contribution'
            )), 400
        
        # Parse target date if provided
        target_date = None
        if target_date_str:
            target_date = _parse_date(target_date_str)
            if not target_date:
                return jsonify(_format_response(
                    success=False,
                    error='Invalid target_date format. Use YYYY-MM-DD'
                )), 400
        
        # Calculate time remaining
        time_remaining = calculate_time_remaining(
            target_amount=target_amount,
            current_amount=current_amount,
            monthly_contribution=monthly_contribution,
            target_date=target_date,
            annual_return=annual_return,
        )
        
        # Add goal_id to response
        time_remaining['goal_id'] = goal_id
        
        return jsonify(_format_response(
            success=True,
            data=time_remaining,
            message='Time remaining calculated successfully'
        )), 200
        
    except Exception as e:
        logger.error(f"Error calculating time remaining: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


@goals_bp.route('/<goal_id>/analysis', methods=['GET'])
def get_goal_analysis_endpoint(goal_id: str):
    """Get comprehensive analysis for a goal.
    
    Query Parameters:
        - goal_name: Goal name (required)
        - target_amount: Target amount (required)
        - current_amount: Current savings (required)
        - target_date: Target date in YYYY-MM-DD format (optional)
        - monthly_contribution: Monthly contribution (default: 0)
        - annual_return: Expected annual return (default: 0.06)
        - goal_type: Type of goal (default: 'SAVINGS')
        
    Returns:
        {
            "success": true,
            "data": {
                "goal_id": str,
                "goal_name": str,
                "progress_percent": float,
                "expected_completion_date": str,
                "monthly_required": float,
                "on_track": bool,
                "priority_recommendation": str,
                ... (full analysis)
            }
        }
        
    Example:
        GET /api/goals/goal-123/analysis?goal_name=Home&target_amount=5000000&current_amount=1500000&monthly_contribution=50000
    """
    try:
        # Get query parameters
        goal_name = request.args.get('goal_name')
        target_amount = request.args.get('target_amount', type=float)
        current_amount = request.args.get('current_amount', type=float, default=0)
        target_date_str = request.args.get('target_date')
        monthly_contribution = request.args.get('monthly_contribution', type=float, default=0)
        annual_return = request.args.get('annual_return', type=float, default=0.06)
        goal_type = request.args.get('goal_type', default='SAVINGS')
        
        # Validate required parameters
        if not goal_name or not target_amount:
            return jsonify(_format_response(
                success=False,
                error='Missing required parameters: goal_name, target_amount'
            )), 400
        
        # Parse target date if provided
        target_date = None
        if target_date_str:
            target_date = _parse_date(target_date_str)
            if not target_date:
                return jsonify(_format_response(
                    success=False,
                    error='Invalid target_date format. Use YYYY-MM-DD'
                )), 400
        
        # Get comprehensive analysis
        analysis = get_goal_progress_analysis(
            goal_id=goal_id,
            goal_name=goal_name,
            target_amount=target_amount,
            current_amount=current_amount,
            target_date=target_date,
            monthly_contribution=monthly_contribution,
            annual_return=annual_return,
            goal_type=goal_type,
        )
        
        return jsonify(_format_response(
            success=True,
            data=analysis,
            message='Goal analysis retrieved successfully'
        )), 200
        
    except Exception as e:
        logger.error(f"Error getting goal analysis: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


# ============================================================================
# GOAL HIGHLIGHTS & BATCH ENDPOINTS
# ============================================================================

@goals_bp.route('/highlights', methods=['POST'])
def get_goals_highlights():
    """Get highlights and metrics across all goals.
    
    Request Body (JSON):
        {
            "goals": [
                {
                    "goal_id": str,
                    "goal_name": str,
                    "target_amount": float,
                    "current_amount": float,
                    "target_date": str (YYYY-MM-DD, optional),
                    "monthly_contribution": float (default: 0),
                    "annual_return": float (default: 0.06),
                    "goal_type": str (default: 'SAVINGS')
                },
                ...
            ]
        }
    
    Returns:
        {
            "success": true,
            "data": {
                "total_goals": int,
                "goals_completed": int,
                "completion_rate": float,
                "goals_on_track": int,
                "goals_behind": int,
                "average_progress": float,
                "highest_priority_goal": {...},
                "closest_completion": {...}
            }
        }
        
    Example:
        POST /api/goals/highlights
        Body: {
            "goals": [
                {
                    "goal_id": "goal-1",
                    "goal_name": "Home",
                    "target_amount": 5000000,
                    "current_amount": 1500000,
                    "monthly_contribution": 50000,
                    "target_date": "2027-12-31"
                },
                ...
            ]
        }
    """
    try:
        # Get request body
        request_data = request.get_json()
        
        if not request_data or 'goals' not in request_data:
            return jsonify(_format_response(
                success=False,
                error='Invalid request body. Expected: {"goals": [...]}'
            )), 400
        
        goals_data = request_data.get('goals', [])
        
        # Process each goal
        goals_analysis = []
        for goal in goals_data:
            try:
                # Parse target date if provided
                target_date = None
                if goal.get('target_date'):
                    target_date = _parse_date(goal['target_date'])
                
                # Get analysis for this goal
                analysis = get_goal_progress_analysis(
                    goal_id=goal.get('goal_id', 'unknown'),
                    goal_name=goal.get('goal_name', 'Unnamed Goal'),
                    target_amount=goal.get('target_amount', 0),
                    current_amount=goal.get('current_amount', 0),
                    target_date=target_date,
                    monthly_contribution=goal.get('monthly_contribution', 0),
                    annual_return=goal.get('annual_return', 0.06),
                    goal_type=goal.get('goal_type', 'SAVINGS'),
                )
                goals_analysis.append(analysis)
                
            except Exception as e:
                logger.warning(f"Error analyzing goal {goal.get('goal_id')}: {str(e)}")
                continue
        
        # Calculate highlights
        highlights = calculate_goal_highlights(goals_analysis)
        
        return jsonify(_format_response(
            success=True,
            data={
                'highlights': highlights,
                'goals_count_processed': len(goals_analysis),
            },
            message='Goal highlights calculated successfully'
        )), 200
        
    except Exception as e:
        logger.error(f"Error calculating highlights: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


@goals_bp.route('/batch-analysis', methods=['POST'])
def batch_goal_analysis():
    """Get analysis for multiple goals in one request.
    
    Request Body (JSON):
        Same as /highlights endpoint
    
    Returns:
        {
            "success": true,
            "data": {
                "goals": [{...analysis for each goal...}],
                "highlights": {...highlights...},
                "total_goals": int
            }
        }
    """
    try:
        # Get request body
        request_data = request.get_json()
        
        if not request_data or 'goals' not in request_data:
            return jsonify(_format_response(
                success=False,
                error='Invalid request body. Expected: {"goals": [...]}'
            )), 400
        
        goals_data = request_data.get('goals', [])
        
        # Process each goal
        goals_analysis = []
        for goal in goals_data:
            try:
                # Parse target date if provided
                target_date = None
                if goal.get('target_date'):
                    target_date = _parse_date(goal['target_date'])
                
                # Get analysis for this goal
                analysis = get_goal_progress_analysis(
                    goal_id=goal.get('goal_id', 'unknown'),
                    goal_name=goal.get('goal_name', 'Unnamed Goal'),
                    target_amount=goal.get('target_amount', 0),
                    current_amount=goal.get('current_amount', 0),
                    target_date=target_date,
                    monthly_contribution=goal.get('monthly_contribution', 0),
                    annual_return=goal.get('annual_return', 0.06),
                    goal_type=goal.get('goal_type', 'SAVINGS'),
                )
                goals_analysis.append(analysis)
                
            except Exception as e:
                logger.warning(f"Error analyzing goal {goal.get('goal_id')}: {str(e)}")
                continue
        
        # Calculate highlights
        highlights = calculate_goal_highlights(goals_analysis)
        
        return jsonify(_format_response(
            success=True,
            data={
                'goals': goals_analysis,
                'highlights': highlights,
                'total_goals': len(goals_analysis),
            },
            message='Batch analysis completed successfully'
        )), 200
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return jsonify(_format_response(
            success=False,
            error=str(e)
        )), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@goals_bp.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request."""
    return jsonify(_format_response(
        success=False,
        error='Bad request: ' + str(error)
    )), 400


@goals_bp.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found."""
    return jsonify(_format_response(
        success=False,
        error='Resource not found'
    )), 404


@goals_bp.errorhandler(500)
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

def register_goals_blueprint(app):
    """Register the goals blueprint with Flask app.
    
    Usage:
        from goals_api import register_goals_blueprint
        register_goals_blueprint(app)
    """
    app.register_blueprint(goals_bp)
    logger.info("Goals API blueprint registered successfully")
