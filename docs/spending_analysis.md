# Spending Intelligence Module Documentation

## Overview

The Spending Intelligence module (`backend/finance/spending_analysis.py`) provides comprehensive transaction analysis to help users understand and optimize their spending patterns. It analyzes budget health, identifies high-spending categories, detects recurring subscriptions, and generates actionable recommendations.

## Core Functions

### 1. `calculate_budget_ratio(monthly_income: float, monthly_expenses: float) -> float`

Calculates the expense-to-income ratio to assess overall budget health.

**Parameters:**
- `monthly_income`: Monthly income in currency units (float)
- `monthly_expenses`: Monthly expenses in currency units (float)

**Returns:**
- Budget ratio as decimal (e.g., 0.50 = 50% spend rate)
- Returns 0.0 if income <= 0

**Formula:**
```
budget_ratio = monthly_expenses / monthly_income
```

**Interpretation Scale:**
| Ratio | Status | Meaning |
|-------|--------|---------|
| 0.00 - 0.30 | EXCELLENT | Spending is very conservative, excellent financial health |
| 0.30 - 0.50 | GOOD | Healthy spending patterns, good control |
| 0.50 - 0.70 | FAIR | Moderate spending, acceptable but room for improvement |
| 0.70 - 1.00 | TIGHT | High spending ratio, limited flexibility |
| > 1.00 | OVER_BUDGET | Expenses exceed income, unsustainable |

**Examples:**
```python
# Good budget manager
calculate_budget_ratio(5000, 2000)  # Returns 0.40 (40% spend)

# Over budget
calculate_budget_ratio(3000, 3500)  # Returns 1.1667 (117% spend)

# Zero income
calculate_budget_ratio(0, 500)      # Returns 0.0 (safe default)
```

### 2. `categorize_budget_ratio(ratio: float) -> Dict[str, str]`

Converts numeric budget ratio to health status with interpretation.

**Parameters:**
- `ratio`: Budget ratio from `calculate_budget_ratio()`

**Returns:**
```python
{
    'status': 'EXCELLENT' | 'GOOD' | 'FAIR' | 'TIGHT' | 'OVER_BUDGET',
    'description': str  # Human-readable explanation
    'color': str        # UI color hint: 'green', 'lightgreen', 'yellow', 'orange', 'red'
}
```

**Example:**
```python
status = categorize_budget_ratio(0.65)
# Returns:
# {
#     'status': 'FAIR',
#     'description': 'Your budget is fair. You are spending 65% of your income...',
#     'color': 'yellow'
# }
```

### 3. `calculate_category_spending_distribution(transactions: List[Transaction], monthly_income: float) -> Dict[str, Dict]`

Analyzes spending by category with multiple metrics.

**Parameters:**
- `transactions`: List of Transaction objects from database
- `monthly_income`: Monthly income for percentage calculations

**Returns:**
```python
{
    'CategoryName': {
        'total_spent': float,           # Total amount in category
        'percentage_of_total': float,   # % of all spending
        'percentage_of_income': float,  # % of monthly income
        'transaction_count': int,       # Number of transactions
        'avg_per_transaction': float    # Average transaction amount
    },
    ...
}
```

**Key Features:**
- Filters to EXPENSE transactions only
- Aggregates by category name
- Calculates both absolute and relative percentages
- Handles zero income gracefully (sets percentage_of_income to 0)

**Example:**
```python
distribution = calculate_category_spending_distribution(transactions, 5000)
# Returns:
# {
#     'Housing': {
#         'total_spent': 1500.00,
#         'percentage_of_total': 52.17,
#         'percentage_of_income': 30.00,
#         'transaction_count': 1,
#         'avg_per_transaction': 1500.00
#     },
#     'Food': {
#         'total_spent': 500.00,
#         'percentage_of_total': 17.39,
#         'percentage_of_income': 10.00,
#         'transaction_count': 3,
#         'avg_per_transaction': 166.67
#     },
#     ...
# }
```

### 4. `detect_high_spending_categories(distribution: Dict, monthly_income: float, thresholds: Optional[Dict] = None) -> List[Dict]`

Identifies spending categories that exceed recommended limits.

**Parameters:**
- `distribution`: Output from `calculate_category_spending_distribution()`
- `monthly_income`: Monthly income reference
- `thresholds`: Optional dict of {'CategoryName': 0.XX} for custom limits (default: recommended percentages)

**Returns:**
```python
[
    {
        'category': str,                    # Category name
        'current_percentage': float,       # Actual % of income
        'recommended_percentage': float,   # Threshold %
        'current_amount': float,           # Actual spending
        'recommended_amount': float,       # Recommended limit
        'overage_amount': float,           # Amount over limit
        'severity': 'LOW' | 'MEDIUM' | 'HIGH',  # Based on overage %
        'message': str                      # Human-readable alert
    },
    ...
]
```

**Default Thresholds** (% of monthly income):
| Category | Default Threshold |
|----------|------------------|
| Housing | 30% |
| Food | 15% |
| Entertainment | 10% |
| Transport | 8% |
| Utilities | 8% |
| Insurance | 10% |
| Healthcare | 5% |
| Other | 5% |

**Severity Calculation:**
```
overage_ratio = (actual_pct - threshold_pct) / threshold_pct

LOW:    overage_ratio <= 10%   (slightly over)
MEDIUM: overage_ratio 10-25%   (moderately over)
HIGH:   overage_ratio > 25%    (significantly over)
```

**Example:**
```python
alerts = detect_high_spending_categories(distribution, 5000)
# If Housing is 35% but threshold is 30%:
# {
#     'category': 'Housing',
#     'current_percentage': 35.0,
#     'recommended_percentage': 30.0,
#     'current_amount': 1750.0,
#     'recommended_amount': 1500.0,
#     'overage_amount': 250.0,
#     'severity': 'LOW',      # 16.7% over threshold
#     'message': 'Housing spending (35% of income) exceeds recommended...'
# }
```

### 5. `detect_recurring_subscription_charges(transactions: List[Transaction], min_occurrences: int = 2) -> List[Dict]`

Identifies likely subscription and recurring charges.

**Parameters:**
- `transactions`: List of Transaction objects
- `min_occurrences`: Minimum number of occurrences to flag as recurring (default: 2)

**Returns:**
```python
[
    {
        'merchant_name': str,           # Merchant/provider name
        'amount': float,                # Transaction amount
        'frequency': str,               # 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUAL'
        'last_charge': date,            # Date of most recent charge
        'next_estimated_charge': date,  # Estimated next charge
        'monthly_cost': float,          # Annualized monthly amount
        'yearly_cost': float,           # Total yearly cost
        'transaction_count': int,       # Number of occurrences
        'flagged_as_recurring': bool    # Tagged with is_recurring=True
    },
    ...
]  # Sorted by yearly_cost descending
```

**Frequency Detection Logic:**
- Groups transactions by (merchant_name, amount)
- Analyzes time intervals between occurrences:
  - **WEEKLY**: 6-8 days apart
  - **MONTHLY**: 28-35 days apart
  - **QUARTERLY**: 88-95 days apart
  - **ANNUAL**: 355-370 days apart
- Includes transactions marked with `is_recurring=True`
- Estimates next charge date based on detected frequency

**Example:**
```python
subscriptions = detect_recurring_subscription_charges(transactions)
# Returns:
# [
#     {
#         'merchant_name': 'Netflix',
#         'amount': 14.99,
#         'frequency': 'MONTHLY',
#         'last_charge': date(2024, 1, 15),
#         'next_estimated_charge': date(2024, 2, 15),
#         'monthly_cost': 14.99,
#         'yearly_cost': 179.88,
#         'transaction_count': 3,
#         'flagged_as_recurring': True
#     },
#     {
#         'merchant_name': 'Gym',
#         'amount': 49.99,
#         'frequency': 'MONTHLY',
#         'last_charge': date(2024, 1, 10),
#         'next_estimated_charge': date(2024, 2, 10),
#         'monthly_cost': 49.99,
#         'yearly_cost': 599.88,
#         'transaction_count': 2,
#         'flagged_as_recurring': True
#     }
# ]
```

### 6. `generate_spending_recommendations(distribution: Dict, alerts: List[Dict], subscriptions: List[Dict], budget_ratio: float) -> List[str]`

Generates actionable recommendations based on spending analysis.

**Parameters:**
- `distribution`: Output from `calculate_category_spending_distribution()`
- `alerts`: Output from `detect_high_spending_categories()`
- `subscriptions`: Output from `detect_recurring_subscription_charges()`
- `budget_ratio`: Output from `calculate_budget_ratio()`

**Returns:**
List of recommendation strings with specific, actionable advice.

**Recommendation Logic:**
1. **Budget Health Recommendations:**
   - If budget_ratio > 0.90: Urgent action to reduce spending
   - If budget_ratio > 0.70: Consider flexible spending reductions
   - If budget_ratio > 1.00: Emergency action required

2. **Category-Based Recommendations:**
   - For each HIGH/MEDIUM severity alert: Specific reduction targets
   - Top 2-3 highest spending alerts: Prioritized suggestions

3. **Subscription Recommendations:**
   - If total yearly subscriptions > $1,000: Review and consolidate
   - If number of subscriptions > 5: Audit for duplicates
   - For each expensive subscription (>$100/year): Consider alternatives

4. **Positive Recommendations:**
   - If budget is healthy: Suggest saving targets
   - Congratulatory messages for good spending discipline

**Example:**
```python
recommendations = generate_spending_recommendations(
    distribution, alerts, subscriptions, 0.75
)
# Returns:
# [
#     "⚠️ URGENT: Your budget ratio is 0.75 (75%). Consider reducing flexible spending...",
#     "Housing is 35% of income (3% over recommended). Consider better rates or location",
#     "Entertainment subscriptions total $215.88/year. Review and consolidate services",
#     "Food spending is 15% - right at recommended level. Maintain current discipline"
# ]
```

## API Integration

The spending analysis functions are integrated into the financial report system and accessible via REST API.

### Full Financial Report
**Endpoint:** `GET /reports/{user_id}`

Returns complete financial report including `spending_analysis` section:
```json
{
    "report_id": "...",
    "user_profile": {...},
    "financial_snapshot": {...},
    "computed_metrics": {...},
    "holdings_summary": {...},
    "goals_analysis": {...},
    "spending_analysis": {
        "available": true,
        "budget_ratio": 0.46,
        "budget_status": "GOOD",
        "budget_status_description": "Your spending is well-controlled...",
        "budget_status_color": "lightgreen",
        "category_distribution": {...},
        "high_spending_alerts": [...],
        "recurring_subscriptions": [...],
        "recommendations": [...]
    },
    "overall_health_score": 72
}
```

### Spending Analysis Only
**Endpoint:** `GET /reports/{user_id}/spending-analysis`

Returns only the spending analysis section without other report components.

**Response:**
```json
{
    "available": true,
    "budget_ratio": 0.46,
    "budget_status": "GOOD",
    "budget_status_description": "Your spending is well-controlled...",
    "budget_status_color": "lightgreen",
    "category_distribution": {
        "Housing": {...},
        "Food": {...},
        "Entertainment": {...}
    },
    "high_spending_alerts": [...],
    "recurring_subscriptions": [...],
    "recommendations": [...]
}
```

## Usage Examples

### Example 1: User with Healthy Budget
```python
# User: $5000/month income, $2300/month expenses
budget_ratio = calculate_budget_ratio(5000, 2300)  # 0.46

distribution = calculate_category_spending_distribution(transactions, 5000)
# {
#     'Housing': {'total_spent': 1500, 'percentage_of_income': 30.0},
#     'Food': {'total_spent': 500, 'percentage_of_income': 10.0},
#     'Entertainment': {'total_spent': 200, 'percentage_of_income': 4.0},
#     ...
# }

alerts = detect_high_spending_categories(distribution, 5000)
# No alerts - all categories within recommended limits

subscriptions = detect_recurring_subscription_charges(transactions)
# [
#     {'merchant_name': 'Netflix', 'yearly_cost': 179.88},
#     {'merchant_name': 'Spotify', 'yearly_cost': 155.88},
# ]
# Total: $335.76/year - manageable

recommendations = generate_spending_recommendations(
    distribution, alerts, subscriptions, 0.46
)
# ["Great job maintaining a healthy budget ratio!", "Keep your current spending discipline"]
```

### Example 2: User with Budget Concerns
```python
# User: $3000/month income, $2700/month expenses
budget_ratio = calculate_budget_ratio(3000, 2700)  # 0.90

status = categorize_budget_ratio(0.90)
# 'status': 'TIGHT' - needs immediate attention

distribution shows:
# 'Entertainment': {'percentage_of_income': 15.0}  # vs 10% recommended
# 'Food': {'percentage_of_income': 25.0}  # vs 15% recommended

alerts = detect_high_spending_categories(distribution, 3000)
# Multiple HIGH severity alerts for Entertainment and Food

recommendations = generate_spending_recommendations(...)
# [
#     "⚠️ URGENT: Budget ratio is 0.90 (90%). You have minimal flexibility...",
#     "Entertainment is 50% over recommended limit. Consider canceling subscriptions.",
#     "Food spending exceeds budget by 66%. Review meal planning strategies.",
# ]
```

## Dashboard Integration

### Streamlit Components

The spending analysis module powers these dashboard sections:

1. **Budget Health Card**
   - Displays budget ratio with color-coded status
   - Shows interpretation of current spending level
   - Quick action buttons for drill-down

2. **Category Spending Pie Chart**
   - Visualizes spending distribution by category
   - Highlights categories with alerts
   - Hover shows spending amounts and percentages

3. **High Spending Alerts**
   - Alert banner with severity indicators
   - Lists categories exceeding recommended percentages
   - Shows overage amounts and recommended adjustments

4. **Subscription Summary**
   - Table of detected recurring charges
   - Total yearly subscription cost
   - Frequency and next charge estimates
   - Action buttons to explore or cancel

5. **Recommendations Section**
   - Priority-ordered action items
   - Category-specific suggestions
   - Subscription optimization tips
   - Positive reinforcement for good behavior

## Performance Considerations

- **Transaction Volume:** Optimized for users with 100-1000 transactions/year
- **Processing Time:** < 100ms for typical users
- **Memory Usage:** Minimal - streaming approach, no intermediate arrays
- **Database Queries:** Single query per report generation
- **Caching:** Results cached in report until next generation

## Error Handling

Functions handle edge cases gracefully:

- **Zero Income:** Returns safe defaults (ratio=0.0, no percentages)
- **No Transactions:** Returns empty distributions, no errors
- **No Data:** Returns available=false indicator
- **Null Values:** Filters gracefully, no crashes
- **Duplicate Amounts:** Grouped intelligently for subscription detection

## Customization

### Custom Spending Thresholds

Override default thresholds when calling detection:
```python
custom_thresholds = {
    'Housing': 0.35,        # 35% instead of default 30%
    'Entertainment': 0.15,  # 15% instead of default 10%
    'Other': 0.20           # Add new category
}

alerts = detect_high_spending_categories(
    distribution, 
    5000,
    thresholds=custom_thresholds
)
```

### Frequency Sensitivity

Adjust subscription detection sensitivity:
```python
# Only flag truly recurring (3+ occurrences)
subscriptions = detect_recurring_subscription_charges(
    transactions, 
    min_occurrences=3
)
```

## Testing

Unit tests cover:
- ✅ All core functions with normal inputs
- ✅ Edge cases (zero income, no transactions)
- ✅ Boundary conditions (threshold matches)
- ✅ Large datasets (100+ transactions)
- ✅ Integration workflow (end-to-end)

Run tests:
```bash
pytest tests/test_spending_analysis.py -v
```

## Future Enhancements

Planned improvements:
- [ ] Seasonal spending pattern detection
- [ ] Budget goal setting and tracking
- [ ] Spending trend analysis (month-over-month)
- [ ] Category-level saving tips (ML-powered)
- [ ] Peer benchmarking (anonymized comparison)
- [ ] Real-time spending alerts
- [ ] Multi-currency support
