"""Goal Progress Tracker - Quick Reference Guide

A quick lookup guide for all functions and their usage.
"""

# ============================================================================
# MODULE: progress_tracker.py
# ============================================================================

"""
Location: backend/finance/progress_tracker.py

MAIN FUNCTIONS:
"""

# 1. calculate_goal_progress()
# ============================
"""
Purpose: Calculate progress percentage towards a goal.

Signature:
    def calculate_goal_progress(target_amount, current_amount) -> Dict

Parameters:
    target_amount (float): Target goal amount. Required: > 0
    current_amount (float): Current amount saved/accumulated. >= 0

Returns:
    {
        'goal_progress_percent': float (0-100),
        'remaining_amount': float,
        'progress_status': str,
        'error': str (if invalid input)
    }

Progress Status Values:
    - "Complete" (100%)
    - "Nearly Complete" (75-99%)
    - "In Progress" (25-74%)
    - "Just Started" (1-24%)
    - "Not Started" (0%)
    - "Invalid Target" (target <= 0)

Example:
    >>> from finance.progress_tracker import calculate_goal_progress
    >>> progress = calculate_goal_progress(500000, 250000)
    >>> print(progress['goal_progress_percent'])  # 50.0
    >>> print(progress['progress_status'])        # "In Progress"
    >>> print(progress['remaining_amount'])       # 250000.0

Use Case:
    - Simple progress tracking
    - Basic goal metrics
    - Progress bar calculations
"""


# 2. calculate_time_remaining()
# ==============================
"""
Purpose: Calculate months/years remaining to complete goal.

Signature:
    def calculate_time_remaining(
        target_amount,
        current_amount,
        monthly_contribution,
        target_date=None,
        annual_return=0.06
    ) -> Dict

Parameters:
    target_amount (float): Target goal amount. Required: > 0
    current_amount (float): Current savings. >= 0
    monthly_contribution (float): Monthly SIP amount. >= 0, Required
    target_date (date): User's target completion date. Optional
    annual_return (float): Expected annual return. Default: 6% (0.06)

Returns:
    {
        'months_remaining': int,
        'years_remaining': float,
        'expected_completion_date': str (YYYY-MM),
        'on_track': bool (true if achievable by target_date),
        'time_until_target_date': int (months),
        'feasible': bool (achievable with current contribution),
        'message': str,
        'error': str (if invalid input)
    }

Example:
    >>> from datetime import date
    >>> time_left = calculate_time_remaining(
    ...     target_amount=500000,
    ...     current_amount=200000,
    ...     monthly_contribution=8000,
    ...     target_date=date(2027, 12, 31)
    ... )
    >>> print(time_left['months_remaining'])       # 31
    >>> print(time_left['expected_completion_date']) # "2028-09"
    >>> print(time_left['on_track'])                # True

Use Case:
    - Calculate goal achievement timeline
    - Check if goal is achievable by target date
    - Determine required monthly contribution
"""


# 3. get_goal_progress_analysis()
# ================================
"""
Purpose: Get comprehensive progress analysis for a single goal.

Signature:
    def get_goal_progress_analysis(
        goal_id,
        goal_name,
        target_amount,
        current_amount,
        target_date,
        monthly_contribution=0,
        annual_return=0.06,
        goal_type=None
    ) -> Dict

Parameters:
    goal_id (str): Unique goal identifier. Required
    goal_name (str): Name of the goal. Required
    target_amount (float): Target amount. Required: > 0
    current_amount (float): Current amount. >= 0
    target_date (date): Target completion date. Optional
    monthly_contribution (float): Monthly contribution. Default: 0
    annual_return (float): Expected return. Default: 6%
    goal_type (str): Type (SAVINGS, INVESTMENT, EDUCATION, etc.). Optional

Returns:
    {
        'goal_id': str,
        'goal_name': str,
        'goal_type': str,
        'progress_percent': float,
        'expected_completion_date': str,
        'months_remaining': int,
        'years_remaining': float,
        'on_track': bool,
        'monthly_required': float,
        'current_monthly_contribution': float,
        'priority_recommendation': str,
        'target_amount': float,
        'current_amount': float,
        'remaining_amount': float,
        'goal_progress': {...},
        'time_remaining': {...}
    }

Recommendation Values:
    - "Completed"
    - "On track"
    - "Increase contribution to ₹X/month to stay on track"
    - "Increase investment frequency"
    - "Prioritize this goal"

Example:
    >>> analysis = get_goal_progress_analysis(
    ...     goal_id="goal-123",
    ...     goal_name="Home",
    ...     target_amount=5000000,
    ...     current_amount=1500000,
    ...     target_date=date(2027, 12, 31),
    ...     monthly_contribution=50000
    ... )
    >>> print(f"Progress: {analysis['progress_percent']}%")      # 30.0%
    >>> print(f"Recommendation: {analysis['priority_recommendation']}")
    >>> print(f"Monthly Required: ₹{analysis['monthly_required']:,.0f}")

Use Case:
    - Dashboard goal cards
    - Comprehensive goal reports
    - Goal recommendations
"""


# 4. calculate_goal_highlights()
# ==============================
"""
Purpose: Calculate key metrics across multiple goals.

Signature:
    def calculate_goal_highlights(goals) -> Dict

Parameters:
    goals (List[Dict]): List of goal analysis dictionaries

Returns:
    {
        'total_goals': int,
        'goals_completed': int,
        'completion_rate': float (0-100),
        'goals_on_track': int,
        'goals_behind': int,
        'average_progress': float,
        'highest_priority_goal': Dict (goal with least progress),
        'closest_completion': Dict (goal closest to completion)
    }

Example:
    >>> goals = [goal1_analysis, goal2_analysis, goal3_analysis]
    >>> highlights = calculate_goal_highlights(goals)
    >>> print(f"Overall: {highlights['average_progress']}% complete")
    >>> print(f"On track: {highlights['goals_on_track']}/{highlights['total_goals']}")
    >>> print(f"Priority: {highlights['highest_priority_goal']['goal_name']}")

Use Case:
    - Dashboard summary cards
    - Overall progress metrics
    - Priority identification
"""


# ============================================================================
# MODULE: goals_api.py
# ============================================================================

"""
Location: backend/routes/goals_api.py

API ENDPOINTS (REST):
"""

# 1. GET /api/goals/<goal_id>/progress
"""
Get progress percentage for a goal.

Query Parameters:
    target_amount (required): Target amount
    current_amount: Current saved amount

Response:
    {
        "success": true/false,
        "data": {goal_progress data},
        "message": str,
        "timestamp": ISO timestamp
    }

Status Code: 200 (success), 400 (bad request), 500 (error)
"""

# 2. GET /api/goals/<goal_id>/time-remaining
"""
Calculate time remaining to goal completion.

Query Parameters:
    target_amount (required)
    current_amount
    monthly_contribution (required)
    target_date: YYYY-MM-DD format
    annual_return: Default 0.06

Status Code: 200, 400, 500
"""

# 3. GET /api/goals/<goal_id>/analysis
"""
Get comprehensive analysis for a single goal.

Query Parameters:
    goal_name (required)
    target_amount (required)
    current_amount
    target_date
    monthly_contribution: Default 0
    annual_return: Default 0.06
    goal_type: Default 'SAVINGS'

Status Code: 200, 400, 500
"""

# 4. POST /api/goals/highlights
"""
Get highlights for multiple goals.

Request Body (JSON):
    {
        "goals": [
            {
                "goal_id": str,
                "goal_name": str,
                "target_amount": float,
                "current_amount": float,
                "monthly_contribution": float,
                "target_date": "YYYY-MM-DD",
                "goal_type": str
            },
            ...
        ]
    }

Status Code: 200, 400, 500
"""

# 5. POST /api/goals/batch-analysis
"""
Get detailed analysis for multiple goals in one request.

Request Body: Same as /highlights

Response includes:
    - goals: Array of goal analysis
    - highlights: Aggregate metrics
    - total_goals: Count processed

Status Code: 200, 400, 500
"""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# _round_currency(value)
# ======================
"""
Round monetary value to 2 decimal places.

Parameters:
    value: Numeric value

Returns:
    float: Rounded to ₹X.XX format

Example:
    >>> _round_currency(12345.678)
    12345.68
"""

# _round_ratio(value, places=2)
# ============================
"""
Round percentage/ratio to specified decimal places.

Parameters:
    value: Numeric value
    places: Decimal places. Default: 2

Returns:
    float: Rounded value

Example:
    >>> _round_ratio(33.3333, places=1)
    33.3
"""


# ============================================================================
# COMMON USAGE PATTERNS
# ============================================================================

"""
PATTERN 1: Single Goal Progress
--------------------------------
from finance.progress_tracker import calculate_goal_progress

progress = calculate_goal_progress(target=100000, current=75000)
# Use: Simple progress bar, progress percentage display


PATTERN 2: Check if Goal is On Track
-------------------------------------
from datetime import date
from finance.progress_tracker import calculate_time_remaining

result = calculate_time_remaining(
    target_amount=500000,
    current_amount=200000,
    monthly_contribution=5000,
    target_date=date(2025, 12, 31)
)

if result['on_track']:
    print("Goal is achievable!")
else:
    print("Need to increase contribution")

# Use: Progress tracking, alerts, notifications


PATTERN 3: Full Dashboard Analysis
-----------------------------------
from finance.progress_tracker import (
    get_goal_progress_analysis,
    calculate_goal_highlights
)

# Step 1: Fetch user goals from database
user_goals = get_user_goals()  # From DB

# Step 2: Analyze each goal
analyses = [
    get_goal_progress_analysis(
        goal_id=g.id,
        goal_name=g.name,
        target_amount=g.target,
        current_amount=g.current,
        target_date=g.target_date,
        monthly_contribution=g.monthly,
        goal_type=g.type
    )
    for g in user_goals
]

# Step 3: Get highlights
highlights = calculate_goal_highlights(analyses)

# Step 4: Render dashboard with analyses and highlights
render_dashboard(analyses, highlights)


PATTERN 4: API Request
---------------------
import requests

# Single goal analysis
response = requests.get(
    'http://localhost:5000/api/goals/goal-1/analysis',
    params={
        'goal_name': 'Home',
        'target_amount': 5000000,
        'current_amount': 1500000,
        'monthly_contribution': 50000
    }
)

if response.json()['success']:
    analysis = response.json()['data']
    print(f"Progress: {analysis['progress_percent']}%")
    print(f"Recommendation: {analysis['priority_recommendation']}")


PATTERN 5: Batch API Analysis
-----------------------------
import requests

goals_data = {
    'goals': [
        {
            'goal_id': 'g1',
            'goal_name': 'Home',
            'target_amount': 5000000,
            'current_amount': 1500000,
            'monthly_contribution': 50000
        },
        {
            'goal_id': 'g2',
            'goal_name': 'Education',
            'target_amount': 1500000,
            'current_amount': 1200000,
            'monthly_contribution': 8000
        }
    ]
}

response = requests.post(
    'http://localhost:5000/api/goals/batch-analysis',
    json=goals_data
)

data = response.json()['data']
print(f"Total goals: {data['highlights']['total_goals']}")
print(f"Average progress: {data['highlights']['average_progress']}%")
"""


# ============================================================================
# ERROR HANDLING
# ============================================================================

"""
COMMON ERRORS:

1. Invalid target amount (<=0):
   Response: {'error': 'Target amount must be positive', ...}
   Fix: Ensure target_amount > 0

2. Invalid date format (not YYYY-MM-DD):
   Response: {'error': 'Invalid target_date format. Use YYYY-MM-DD', ...}
   Fix: Use proper date format in API calls

3. Missing required parameters:
   Response: {'error': 'Missing required parameters: X, Y', ...}
   Fix: Include all required parameters

4. No monthly contribution but expecting goal achievement:
   Response: {'feasible': false, 'error': 'No monthly contribution...'}
   Fix: Provide positive monthly_contribution or adjust parameters
"""


# ============================================================================
# TESTING
# ============================================================================

"""
Run all tests:
    cd backend/finance
    python test_progress_tracker.py

Test Coverage:
    ✓ Goal progress calculations
    ✓ Time remaining calculations
    ✓ Comprehensive analysis
    ✓ Goal highlights
    ✓ Edge cases (negative values, zero contribution, etc.)
    ✓ Multiple goal scenarios

All tests pass with sample data:
    - Home purchase: 30% progress, 42 months remaining
    - Education: 80% progress, 5 months remaining
    - Vacation: 100% complete
"""


# ============================================================================
# INTEGRATION CHECKLIST
# ============================================================================

"""
☐ 1. Import progress_tracker module
☐ 2. Register goals_api blueprint
☐ 3. Create Goal database model
☐ 4. Implement goal CRUD endpoints
☐ 5. Add progress update functionality
☐ 6. Build dashboard frontend
☐ 7. Connect API endpoints to frontend
☐ 8. Add caching for highlights
☐ 9. Implement notifications/alerts
☐ 10. Add goal recommendations
☐ 11. Performance testing
☐ 12. Error handling & validation
☐ 13. Documentation & help
☐ 14. User testing
"""


# ============================================================================
# KEY FORMULAS
# ============================================================================

"""
Progress %:
    progress = (current / target) × 100
    Min: 0%, Max: 100%

Monthly Return:
    r_monthly = (1 + r_annual)^(1/12) - 1
    Example: 6% annual = 0.4868% monthly

Future Value (SIP):
    FV = PV × (1 + r)^n + PMT × [((1 + r)^n - 1) / r]
    Where:
    - FV: Future value (target)
    - PV: Present value (current)
    - r: Monthly return
    - n: Number of months
    - PMT: Monthly payment

Required Monthly Payment:
    PMT = (Target - Current) / [(((1+r)^n - 1) / r)]
"""


# ============================================================================
# PERFORMANCE NOTES
# ============================================================================

"""
Time Complexity:
    calculate_goal_progress: O(1)
    calculate_time_remaining: O(log n) where n = months to goal
    calculate_goal_highlights: O(m) where m = number of goals
    
Space Complexity: O(1) for all functions (constant extra space)

Optimization Tips:
    1. Cache goal highlights if frequently accessed
    2. Batch API calls for multiple goals
    3. Use annual_return=0 for savings without returns
    4. Adjust monthly_return accuracy for precision
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nFor detailed integration guide, see INTEGRATION_GUIDE.md")
