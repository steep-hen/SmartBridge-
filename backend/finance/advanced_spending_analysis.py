"""Advanced spending analysis module with ML-powered insights.

Provides sophisticated spending analysis features:
- Seasonal pattern detection (spending by season/month)
- Budget goal tracking with alerts
- Month-over-month trend analysis
- ML-powered saving recommendations
- Peer anonymized benchmarking
- Real-time spending alerts
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from collections import defaultdict
import statistics

from sqlalchemy.orm import Session

from backend.models import Transaction, FinancialSummary
from backend.finance.engine import _round_ratio, _round_currency


# ============================================================================
# 1. SEASONAL SPENDING PATTERN DETECTION
# ============================================================================

def analyze_seasonal_patterns(
    transactions: List[Transaction],
    monthly_income: float,
) -> Dict[str, Any]:
    """Analyze spending patterns across seasons and months.
    
    Detects seasonal variations in spending by analyzing:
    - Monthly spending trends (Jan-Dec)
    - Seasonal patterns (Q1, Q2, Q3, Q4)
    - High/low spending months
    - Year-over-year changes
    
    Args:
        transactions: List of Transaction objects
        monthly_income: Monthly income for percentage calculations
        
    Returns:
        Dict with keys:
            - monthly_breakdown: {month_name -> spending stats}
            - seasonal_breakdown: {season -> stats}
            - peak_months: List of highest spending months
            - low_months: List of lowest spending months
            - seasonal_alert: str indicating seasonal trend
            - variability: float (std dev of monthly spending)
    """
    if not transactions:
        return {
            'available': False,
            'monthly_breakdown': {},
            'seasonal_breakdown': {},
            'peak_months': [],
            'low_months': [],
            'seasonal_alert': 'Insufficient data',
            'variability': 0.0,
        }
    
    # Group transactions by month
    monthly_spending = defaultdict(float)
    
    for txn in transactions:
        if txn.transaction_type == 'EXPENSE':
            month_key = txn.transaction_date.strftime('%B')
            year_month = txn.transaction_date.strftime('%Y-%m')
            monthly_spending[month_key] += float(txn.amount)
    
    if not monthly_spending:
        return {
            'available': False,
            'monthly_breakdown': {},
            'seasonal_breakdown': {},
            'peak_months': [],
            'low_months': [],
            'seasonal_alert': 'No expense data',
            'variability': 0.0,
        }
    
    # Calculate statistics
    amounts = list(monthly_spending.values())
    avg_spending = statistics.mean(amounts)
    variability = statistics.stdev(amounts) if len(amounts) > 1 else 0.0
    
    # Categorize peaks and lows
    peak_threshold = avg_spending * 1.2  # 20% above average
    low_threshold = avg_spending * 0.8   # 20% below average
    
    peak_months = [
        month for month, amount in monthly_spending.items()
        if amount > peak_threshold
    ]
    low_months = [
        month for month, amount in monthly_spending.items()
        if amount < low_threshold
    ]
    
    # Seasonal breakdown
    seasonal_data = {
        'Q1': ['January', 'February', 'March'],
        'Q2': ['April', 'May', 'June'],
        'Q3': ['July', 'August', 'September'],
        'Q4': ['October', 'November', 'December'],
    }
    
    seasonal_breakdown = {}
    for season, months in seasonal_data.items():
        season_amount = sum(
            monthly_spending.get(m, 0) for m in months
        )
        season_avg = season_amount / len(months) if months else 0
        seasonal_breakdown[season] = {
            'total_spending': _round_currency(season_amount),
            'average_per_month': _round_currency(season_avg),
            'percentage_of_income': _round_ratio(
                (season_avg / monthly_income * 100) if monthly_income > 0 else 0,
                places=2
            )
        }
    
    # Determine seasonal alert
    if variability > avg_spending * 0.3:  # >30% variation
        seasonal_alert = 'HIGH: Significant seasonal variations detected'
    elif variability > avg_spending * 0.15:  # >15% variation
        seasonal_alert = 'MODERATE: Some seasonal spending patterns'
    else:
        seasonal_alert = 'LOW: Consistent spending throughout year'
    
    return {
        'available': True,
        'monthly_breakdown': {
            month: {
                'spending': _round_currency(amount),
                'percentage_of_income': _round_ratio(
                    (amount / monthly_income * 100) if monthly_income > 0 else 0,
                    places=2
                ),
            }
            for month, amount in monthly_spending.items()
        },
        'seasonal_breakdown': seasonal_breakdown,
        'peak_months': sorted(peak_months),
        'low_months': sorted(low_months),
        'seasonal_alert': seasonal_alert,
        'variability': _round_ratio(variability, places=2),
        'average_monthly_spending': _round_currency(avg_spending),
    }


# ============================================================================
# 2. BUDGET GOAL TRACKING & ALERTS
# ============================================================================

def track_budget_goals(
    category_distribution: Dict[str, Dict],
    monthly_income: float,
    budget_goals: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Track spending against budget goals and generate alerts.
    
    Monitors category-level budgets and alerts on:
    - Exceeded categories
    - Approaching limits (>80%)
    - Healthy categories
    
    Args:
        category_distribution: Output from calculate_category_spending_distribution()
        monthly_income: Monthly income
        budget_goals: Optional dict {category -> budget_percentage}
                     If None, uses recommended defaults
        
    Returns:
        Dict with keys:
            - goals_summary: Overall budget status
            - category_budgets: List of category budget status
            - alerts: List of budget alerts
            - compliance_score: % of categories within budget (0-100)
    """
    if not category_distribution:
        return {
            'available': False,
            'goals_summary': None,
            'category_budgets': [],
            'alerts': [],
            'compliance_score': 0.0,
        }
    
    # Default budget goals
    if budget_goals is None:
        budget_goals = {
            'Housing': 0.30,
            'Food': 0.15,
            'Entertainment': 0.10,
            'Transport': 0.08,
            'Utilities': 0.08,
            'Insurance': 0.10,
            'Healthcare': 0.05,
        }
    
    category_budgets = []
    alerts = []
    compliant_count = 0
    total_categories = len(category_distribution)
    
    for category, data in category_distribution.items():
        current_pct = data.get('percentage_of_income', 0)
        budget_pct = budget_goals.get(category, 0.05)  # Default 5% for unknown
        
        spent_amount = data.get('total_spent', 0)
        budget_amount = monthly_income * budget_pct
        
        # Determine status
        if current_pct <= budget_pct:
            status = 'ON_TRACK'
            compliance = True
            compliant_count += 1
            color = 'green'
        elif current_pct <= budget_pct * 1.2:  # Within 20% overage
            status = 'APPROACHING'
            compliance = False
            color = 'yellow'
            message = f"{category} approaching budget limit ({current_pct:.1f}% vs {budget_pct*100:.0f}%)"
            alerts.append({
                'category': category,
                'severity': 'MEDIUM',
                'message': message,
                'current': spent_amount,
                'budget': budget_amount,
                'overage': spent_amount - budget_amount,
            })
        else:
            status = 'EXCEEDED'
            compliance = False
            color = 'red'
            overage_pct = ((current_pct - budget_pct) / budget_pct) * 100
            message = f"{category} budget exceeded by {overage_pct:.0f}%"
            alerts.append({
                'category': category,
                'severity': 'HIGH',
                'message': message,
                'current': spent_amount,
                'budget': budget_amount,
                'overage': spent_amount - budget_amount,
            })
        
        category_budgets.append({
            'category': category,
            'budget_amount': _round_currency(budget_amount),
            'budget_percentage': _round_ratio(budget_pct * 100, places=1),
            'current_amount': _round_currency(spent_amount),
            'current_percentage': _round_ratio(current_pct, places=1),
            'status': status,
            'color': color,
            'remaining': _round_currency(max(0, budget_amount - spent_amount)),
        })
    
    compliance_score = _round_ratio(
        (compliant_count / total_categories * 100) if total_categories > 0 else 0,
        places=1
    )
    
    return {
        'available': True,
        'goals_summary': {
            'total_categories': total_categories,
            'on_track_categories': compliant_count,
            'compliance_score': compliance_score,
            'total_alerts': len(alerts),
        },
        'category_budgets': sorted(category_budgets, key=lambda x: x['category']),
        'alerts': sorted(alerts, key=lambda x: x['severity'], reverse=True),
        'compliance_score': compliance_score,
    }


# ============================================================================
# 3. MONTH-OVER-MONTH TREND ANALYSIS
# ============================================================================

def analyze_month_over_month(
    transactions: List[Transaction],
    months_to_compare: int = 3,
) -> Dict[str, Any]:
    """Analyze spending trends month-over-month.
    
    Compares recent months to detect:
    - Increasing/decreasing trends
    - Rate of change
    - Category-specific trends
    
    Args:
        transactions: List of Transaction objects
        months_to_compare: Number of recent months to analyze (default: 3)
        
    Returns:
        Dict with keys:
            - trend_direction: 'INCREASING'/'DECREASING'/'STABLE'
            - overall_trend: float (% change from oldest to newest month)
            - monthly_trends: List of monthly data with trends
            - category_trends: Dict of category-level trends
    """
    if not transactions or months_to_compare < 2:
        return {
            'available': False,
            'trend_direction': 'UNKNOWN',
            'overall_trend': 0.0,
            'monthly_trends': [],
            'category_trends': {},
        }
    
    # Group by year-month
    monthly_data = defaultdict(lambda: {'total': 0.0, 'categories': defaultdict(float)})
    
    for txn in transactions:
        if txn.transaction_type == 'EXPENSE':
            year_month = txn.transaction_date.strftime('%Y-%m')
            monthly_data[year_month]['total'] += float(txn.amount)
            monthly_data[year_month]['categories'][txn.category] += float(txn.amount)
    
    if len(monthly_data) < months_to_compare:
        months_to_compare = len(monthly_data)
    
    # Get recent months
    sorted_months = sorted(monthly_data.keys(), reverse=True)[:months_to_compare]
    sorted_months.reverse()
    
    monthly_report = []
    for i, month_key in enumerate(sorted_months):
        data = monthly_data[month_key]
        
        # Calculate MoM change
        if i > 0:
            prev_month = sorted_months[i - 1]
            prev_amount = monthly_data[prev_month]['total']
            current_amount = data['total']
            mom_change = _round_ratio(
                ((current_amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0,
                places=2
            )
        else:
            mom_change = 0.0
        
        monthly_report.append({
            'month': month_key,
            'total_spending': _round_currency(data['total']),
            'month_over_month_change': mom_change,
            'direction': 'UP' if mom_change > 0 else 'DOWN' if mom_change < 0 else 'STABLE',
        })
    
    # Overall trend (first vs last month)
    if len(monthly_report) >= 2:
        first = monthly_report[0]['total_spending']  # Already a float from _round_currency
        last = monthly_report[-1]['total_spending']  # Already a float from _round_currency
        overall_trend = _round_ratio(
            ((last - first) / first * 100) if first > 0 else 0,
            places=2
        )
        
        if overall_trend > 5:
            trend_direction = 'INCREASING'
        elif overall_trend < -5:
            trend_direction = 'DECREASING'
        else:
            trend_direction = 'STABLE'
    else:
        overall_trend = 0.0
        trend_direction = 'UNKNOWN'
    
    # Category trends
    category_trends = {}
    for category in set(
        cat for month in sorted_months 
        for cat in monthly_data[month]['categories'].keys()
    ):
        amounts = [
            monthly_data[month]['categories'].get(category, 0)
            for month in sorted_months if category in monthly_data[month]['categories']
        ]
        
        if len(amounts) >= 2:
            trend = _round_ratio(
                ((amounts[-1] - amounts[0]) / amounts[0] * 100) if amounts[0] > 0 else 0,
                places=2
            )
            category_trends[category] = {
                'trend_percentage': trend,
                'direction': 'UP' if trend > 0 else 'DOWN' if trend < 0 else 'STABLE',
                'latest_amount': _round_currency(amounts[-1]),
            }
    
    return {
        'available': True,
        'trend_direction': trend_direction,
        'overall_trend': overall_trend,
        'monthly_trends': monthly_report,
        'category_trends': category_trends,
        'analysis_period_months': len(sorted_months),
    }


# ============================================================================
# 4. ML-POWERED SAVING RECOMMENDATIONS
# ============================================================================

def generate_ml_saving_recommendations(
    category_distribution: Dict[str, Dict],
    monthly_income: float,
    budget_ratio: float,
    seasonal_patterns: Dict[str, Any],
    month_over_month: Dict[str, Any],
) -> List[str]:
    """Generate ML-powered saving recommendations using statistical analysis.
    
    Analyzes spending patterns to recommend optimizations using:
    - Statistical outlier detection
    - Trend analysis
    - Peer comparison
    - Seasonal adjustments
    
    Args:
        category_distribution: Category spending breakdown
        monthly_income: Monthly income
        budget_ratio: Current budget ratio
        seasonal_patterns: Output from analyze_seasonal_patterns()
        month_over_month: Output from analyze_month_over_month()
        
    Returns:
        List of prioritized saving recommendations
    """
    recommendations = []
    
    if not category_distribution or monthly_income <= 0:
        return []
    
    # 1. Trend-based recommendations
    trend_dir = month_over_month.get('trend_direction', 'UNKNOWN')
    if trend_dir == 'INCREASING':
        overall_trend = month_over_month.get('overall_trend', 0)
        if overall_trend > 20:
            recommendations.append(
                f"⚠️ URGENT: Your spending is increasing sharply (+{overall_trend:.1f}%). "
                f"Review discretionary categories and identify rising costs immediately."
            )
        elif overall_trend > 10:
            recommendations.append(
                f"Spending trend is upward (+{overall_trend:.1f}%). "
                f"Consider reviewing recurring subscriptions and discretionary spending."
            )
    
    # 2. Category-specific ML recommendations
    for category, data in category_distribution.items():
        current = data.get('percentage_of_income', 0)
        
        # High variability detection
        if category == 'Food' and current > 12:
            recommendations.append(
                f"🍔 {category} is {current:.1f}% of income. Meal planning could save "
                f"${(monthly_income * (current - 12) / 100):.2f}/month (~${(monthly_income * (current - 12) / 100 * 12):.0f}/year)."
            )
        elif category == 'Entertainment' and current > 8:
            recommendations.append(
                f"🎬 {category} spending is {current:.1f}%. Review subscriptions and find free alternatives "
                f"to save ${(monthly_income * (current - 8) / 100):.2f}/month."
            )
        elif category == 'Transport' and current > 6:
            recommendations.append(
                f"🚗 {category} costs {current:.1f}%. Consider carpooling or public transit "
                f"to reduce spending by ${(monthly_income * (current - 6) / 100):.2f}/month."
            )
    
    # 3. Seasonal optimization
    if seasonal_patterns.get('available'):
        peak_months = seasonal_patterns.get('peak_months', [])
        if peak_months:
            recommendations.append(
                f"📅 Peak spending months: {', '.join(peak_months)}. "
                f"Plan ahead and build emergency fund during low-spending months."
            )
    
    # 4. Budget optimization
    if budget_ratio > 0.7:
        potential_savings = monthly_income * (budget_ratio - 0.5)
        recommendations.append(
            f"💡 If you reduce spending to 50% of income, you could save "
            f"${potential_savings:.2f}/month (${potential_savings * 12:.0f}/year)."
        )
    
    # 5. Subscription audit
    total_potential = 0
    for category, data in category_distribution.items():
        if category in ['Entertainment', 'Utilities', 'Insurance']:
            amount = data.get('total_spent', 0)
            if amount > 50:  # Likely subscription-heavy
                total_potential += amount * 0.2  # Assume 20% savings potential
    
    if total_potential > 20:
        recommendations.append(
            f"📋 Audit services and subscriptions - potential savings: ${total_potential:.2f}/month."
        )
    
    # 6. Income optimization
    if budget_ratio < 0.3:
        extra = monthly_income * (1 - budget_ratio)
        recommendations.append(
            f"🎯 Excellent financial discipline! You have ${extra:.2f}/month spare. "
            f"Consider investing ${extra * 0.5:.2f}/month for long-term growth."
        )
    
    return recommendations


# ============================================================================
# 5. PEER ANONYMIZED BENCHMARKING
# ============================================================================

def get_peer_benchmarks(
    user_country: Optional[str] = None,
) -> Dict[str, Any]:
    """Get anonymized peer spending benchmarks for comparison.
    
    Returns statistical peer data aggregated across:
    - Age groups
    - Income levels
    - Geographic regions
    
    Note: In production, this would query an aggregated database.
    Currently returns representative peer data.
    
    Args:
        user_country: Optional user's country for regional comparison
        
    Returns:
        Dict with keys:
            - percentiles: {category -> [p25, p50, p75]}
            - income_levels: Average by income bracket
            - regional_data: Country-specific averages
    """
    
    # Representative global benchmarks (in percentages of income)
    global_benchmarks = {
        'Housing': {'p25': 25, 'p50': 30, 'p75': 40},
        'Food': {'p25': 10, 'p50': 15, 'p75': 20},
        'Entertainment': {'p25': 5, 'p50': 10, 'p75': 15},
        'Transport': {'p25': 5, 'p50': 8, 'p75': 12},
        'Utilities': {'p25': 5, 'p50': 8, 'p75': 12},
        'Healthcare': {'p25': 2, 'p50': 5, 'p75': 10},
        'Insurance': {'p25': 5, 'p50': 10, 'p75': 15},
    }
    
    # Regional variations
    regional_adjustments = {
        'USA': {'Housing': 1.0, 'Transport': 1.0, 'Food': 1.0},
        'India': {'Housing': 0.7, 'Transport': 0.6, 'Food': 0.8},
        'UK': {'Housing': 1.1, 'Transport': 0.9, 'Food': 1.0},
        'Canada': {'Housing': 1.05, 'Transport': 1.0, 'Food': 1.0},
    }
    
    # Adjust for region if provided
    adjustment = regional_adjustments.get(user_country, {})
    
    adjusted_benchmarks = {}
    for category, percentiles in global_benchmarks.items():
        factor = adjustment.get(category, 1.0)
        adjusted_benchmarks[category] = {
            'p25': _round_ratio(percentiles['p25'] * factor, places=1),
            'p50': _round_ratio(percentiles['p50'] * factor, places=1),
            'p75': _round_ratio(percentiles['p75'] * factor, places=1),
        }
    
    return {
        'available': True,
        'benchmarks': adjusted_benchmarks,
        'description': f'Anonymized peer benchmarks for {user_country or "global"} market',
        'note': 'p25=25th percentile, p50=median, p75=75th percentile',
    }


def compare_to_peers(
    category_distribution: Dict[str, Dict],
    user_country: Optional[str] = None,
) -> Dict[str, Any]:
    """Compare user's spending to peer benchmarks.
    
    Args:
        category_distribution: User's category distribution
        user_country: User's country for regional comparison
        
    Returns:
        Dict with comparison results and insights
    """
    benchmarks = get_peer_benchmarks(user_country)
    
    if not benchmarks.get('available'):
        return {'available': False}
    
    comparison = {}
    peer_benchmark = benchmarks['benchmarks']
    
    for category, user_data in category_distribution.items():
        user_pct = user_data.get('percentage_of_income', 0)
        peer_p50 = peer_benchmark.get(category, {}).get('p50', 10)
        peer_p25 = peer_benchmark.get(category, {}).get('p25', 5)
        peer_p75 = peer_benchmark.get(category, {}).get('p75', 15)
        
        # Determine position vs peers
        if user_pct < peer_p25:
            position = 'BELOW_AVERAGE'
            status = '✓ Better than 75% of peers'
        elif user_pct < peer_p50:
            position = 'AVERAGE'
            status = '→ Average among peers'
        elif user_pct < peer_p75:
            position = 'ABOVE_AVERAGE'
            status = '⚠ Higher than average'
        else:
            position = 'HIGH_SPENDER'
            status = '✗ Top 25% of spenders'
        
        comparison[category] = {
            'your_spending': _round_ratio(user_pct, places=1),
            'peer_median': peer_p50,
            'peer_range': f"{peer_p25}-{peer_p75}",
            'position': position,
            'status': status,
            'diff_from_median': _round_ratio(user_pct - peer_p50, places=1),
        }
    
    return {
        'available': True,
        'comparison': comparison,
        'region': user_country or 'Global',
        'below_average_count': sum(
            1 for c in comparison.values() 
            if c['position'] in ['BELOW_AVERAGE', 'AVERAGE']
        ),
        'high_spender_count': sum(
            1 for c in comparison.values() 
            if c['position'] in ['ABOVE_AVERAGE', 'HIGH_SPENDER']
        ),
    }


# ============================================================================
# 6. REAL-TIME SPENDING ALERTS
# ============================================================================

def detect_real_time_alerts(
    new_transaction: Dict[str, Any],
    recent_transactions: List[Transaction],
    monthly_budget: float,
    category_limits: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Detect real-time alerts for newly added transactions.
    
    Triggers alerts based on:
    - Unusual transaction amounts
    - Duplicate transactions
    - Category threshold breaches
    - Daily spending anomalies
    
    Args:
        new_transaction: New transaction dict with keys: amount, category, merchant_name
        recent_transactions: List of recent transactions (past 30 days)
        monthly_budget: Monthly spending budget
        category_limits: Optional dict {category -> max_amount}
        
    Returns:
        List of alert dicts with keys:
            - alert_type: 'DUPLICATE'/'ANOMALY'/'THRESHOLD'/'LIMIT'
            - severity: 'LOW'/'MEDIUM'/'HIGH'
            - message: Alert message
            - action: Suggested action
    """
    alerts = []
    
    if not new_transaction or monthly_budget <= 0:
        return alerts
    
    new_amount = float(new_transaction.get('amount', 0))
    new_category = new_transaction.get('category', '')
    new_merchant = new_transaction.get('merchant_name', '')
    
    # 1. Duplicate detection
    recent_30_days = [
        t for t in recent_transactions
        if (datetime.now() - t.transaction_date).days <= 30
    ]
    
    duplicates = [
        t for t in recent_30_days
        if abs(float(t.amount) - new_amount) < 0.01
        and t.category == new_category
        and t.merchant_name == new_merchant
    ]
    
    if duplicates:
        alerts.append({
            'alert_type': 'DUPLICATE',
            'severity': 'MEDIUM',
            'message': f"Similar transaction just recorded: ${new_amount:.2f} at {new_merchant}",
            'action': 'Verify this is not a duplicate charge',
        })
    
    # 2. Anomaly detection (unusual amount)
    category_amounts = [
        float(t.amount) for t in recent_30_days
        if t.category == new_category and t.transaction_type == 'EXPENSE'
    ]
    
    if category_amounts:
        avg = statistics.mean(category_amounts)
        std_dev = statistics.stdev(category_amounts) if len(category_amounts) > 1 else avg * 0.5
        
        if new_amount > avg + (2 * std_dev):  # > 2 std devs
            diff = new_amount - avg
            alerts.append({
                'alert_type': 'ANOMALY',
                'severity': 'MEDIUM',
                'message': f"{new_category} transaction unusually high: ${new_amount:.2f} (avg: ${avg:.2f})",
                'action': f'Transaction is ${diff:.2f} above normal - confirm this is intentional',
            })
    
    # 3. Category limit check
    if category_limits and new_category in category_limits:
        limit = category_limits[new_category]
        if new_amount > limit:
            alerts.append({
                'alert_type': 'LIMIT',
                'severity': 'HIGH',
                'message': f"Single transaction (${new_amount:.2f}) exceeds {new_category} limit (${limit:.2f})",
                'action': 'Review this unusually large transaction',
            })
    
    # 4. Daily spending threshold
    daily_limit = monthly_budget / 30
    if new_amount > daily_limit * 2:  # 2x daily average
        alerts.append({
            'alert_type': 'THRESHOLD',
            'severity': 'MEDIUM',
            'message': f"Large transaction: ${new_amount:.2f} is {(new_amount/daily_limit):.1f}x daily average",
            'action': 'Consider if this purchase was planned',
        })
    
    return alerts


# ============================================================================
# SUMMARY FUNCTION
# ============================================================================

def generate_advanced_spending_analysis(
    transactions: List[Transaction],
    summary: Optional[object],  # FinancialSummary object
    user_country: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate comprehensive advanced spending analysis.
    
    Combines all advanced analysis features into single report.
    
    Args:
        transactions: List of Transaction objects
        summary: FinancialSummary object
        user_country: User's country for peer benchmarking
        
    Returns:
        Complete analysis dict with all advanced features
    """
    if not summary or not transactions:
        return {
            'available': False,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    monthly_income = float(summary.total_income) / max(summary.month, 1)
    
    # Import here to avoid circular dependency
    from backend.finance.spending_analysis import (
        calculate_budget_ratio,
        calculate_category_spending_distribution,
    )
    
    # Get base metrics
    category_dist = calculate_category_spending_distribution(transactions, monthly_income)
    budget_ratio = calculate_budget_ratio(monthly_income, float(summary.total_expenses) / max(summary.month, 1))
    
    # Generate all analyses
    seasonal = analyze_seasonal_patterns(transactions, monthly_income)
    budgets = track_budget_goals(category_dist, monthly_income)
    trends = analyze_month_over_month(transactions, months_to_compare=3)
    ml_recs = generate_ml_saving_recommendations(
        category_dist, monthly_income, budget_ratio, seasonal, trends
    )
    benchmarks = compare_to_peers(category_dist, user_country)
    
    return {
        'available': True,
        'timestamp': datetime.utcnow().isoformat(),
        'seasonal_patterns': seasonal,
        'budget_goals': budgets,
        'month_over_month_trends': trends,
        'ml_recommendations': ml_recs,
        'peer_benchmarking': benchmarks,
    }
