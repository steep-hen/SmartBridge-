"""Spending Intelligence Module - Transaction pattern analysis and insights.

This module analyzes user transaction patterns, identifies spending behaviors,
detects budget overruns, and suggests optimization opportunities.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from sqlalchemy.orm import Session

from backend.models import Transaction, FinancialSummary
from backend.finance.engine import _round_ratio, _round_currency


def calculate_budget_ratio(monthly_income: float, monthly_expenses: float) -> float:
    """Calculate budget ratio (expense to income ratio).
    
    Budget Ratio = Monthly Expenses / Monthly Income
    
    Interpretation:
    - 0.0-0.3: Excellent (under 30% committed)
    - 0.3-0.5: Good (30-50% committed)
    - 0.5-0.7: Fair (50-70% committed)
    -\0.7-1.0: Tight (70-100% committed)
    - 1.0+: Over budget (spending more than earning)
    
    Args:
        monthly_income: Monthly income amount
        monthly_expenses: Monthly expense amount
        
    Returns:
        float: Budget ratio (0.0-1.0+ range)
    """
    if monthly_income <= 0:
        return 0.0
    
    ratio = monthly_expenses / monthly_income
    return _round_ratio(ratio, places=4)


def categorize_budget_ratio(ratio: float) -> Dict[str, str]:
    """Categorize budget ratio into health status.
    
    Args:
        ratio: Budget ratio value
        
    Returns:
        dict with 'status' and 'description'
    """
    if ratio <= 0.3:
        return {
            'status': 'EXCELLENT',
            'description': 'Well below healthy spending threshold',
            'color': 'green'
        }
    elif ratio <= 0.5:
        return {
            'status': 'GOOD',
            'description': 'Healthy spending ratio',
            'color': 'lightgreen'
        }
    elif ratio <= 0.7:
        return {
            'status': 'FAIR',
            'description': 'Moderate spending ratio, monitor closely',
            'color': 'yellow'
        }
    elif ratio <= 1.0:
        return {
            'status': 'TIGHT',
            'description': 'Little room for emergencies',
            'color': 'orange'
        }
    else:
        return {
            'status': 'OVER_BUDGET',
            'description': 'Spending exceeds income',
            'color': 'red'
        }


def calculate_category_spending_distribution(
    transactions: List[Transaction],
    monthly_income: float = 0.0
) -> Dict[str, Dict[str, float]]:
    """Calculate spending distribution by category.
    
    Aggregates transactions by category and calculates total spent
    and percentage of monthly income for each.
    
    Args:
        transactions: List of Transaction objects
        monthly_income: Monthly income (for percentage calculation)
        
    Returns:
        dict mapping category -> {
            'total_spent': float,
            'percentage_of_income': float,
            'transaction_count': int,
            'avg_per_transaction': float
        }
    """
    if not transactions:
        return {}
    
    # Filter to expense transactions only
    expense_transactions = [
        t for t in transactions
        if t.transaction_type == 'EXPENSE'
    ]
    
    if not expense_transactions:
        return {}
    
    # Aggregate by category
    category_aggregates = {}
    
    for transaction in expense_transactions:
        category = transaction.category or 'Other'
        amount = float(transaction.amount)
        
        if category not in category_aggregates:
            category_aggregates[category] = {
                'total_spent': 0.0,
                'transaction_count': 0,
                'transactions': []
            }
        
        category_aggregates[category]['total_spent'] += amount
        category_aggregates[category]['transaction_count'] += 1
        category_aggregates[category]['transactions'].append(amount)
    
    # Calculate percentages and additional metrics
    total_expenses = sum(cat['total_spent'] for cat in category_aggregates.values())
    
    result = {}
    for category, data in category_aggregates.items():
        total_spent = _round_currency(data['total_spent'])
        pct_of_total = (data['total_spent'] / total_expenses * 100) if total_expenses > 0 else 0.0
        pct_of_income = (data['total_spent'] / monthly_income * 100) if monthly_income > 0 else 0.0
        avg_per_txn = (data['total_spent'] / data['transaction_count']) if data['transaction_count'] > 0 else 0.0
        
        result[category] = {
            'total_spent': total_spent,
            'percentage_of_total': _round_ratio(pct_of_total, places=1),
            'percentage_of_income': _round_ratio(pct_of_income, places=1),
            'transaction_count': data['transaction_count'],
            'avg_per_transaction': _round_currency(avg_per_txn),
        }
    
    return result


def detect_high_spending_categories(
    distribution: Dict[str, Dict[str, float]],
    monthly_income: float,
    thresholds: Optional[Dict[str, float]] = None
) -> List[Dict[str, str]]:
    """Detect spending categories that exceed recommended thresholds.
    
    Default thresholds as percentage of income:
    - Housing: 30%
    - Food: 15%
    - Transportation: 8%
    - Entertainment: 10%
    - Utilities: 8%
    - Insurance: 10%
    - Healthcare: 5%
    - Other: 5%
    
    Args:
        distribution: Category distribution dict (from calculate_category_spending_distribution)
        monthly_income: Monthly income (for threshold calculation)
        thresholds: Optional custom thresholds dict {category: percentage}
        
    Returns:
        List of warnings/alerts for overspent categories
    """
    if monthly_income <= 0 or not distribution:
        return []
    
    # Default thresholds (as % of income)
    default_thresholds = {
        'Housing': 30,
        'Rent': 30,
        'Mortgage': 30,
        'Food': 15,
        'Groceries': 15,
        'Entertainment': 10,
        'Transport': 8,
        'Transportation': 8,
        'Utilities': 8,
        'Insurance': 10,
        'Healthcare': 5,
        'Health': 5,
        'Dining': 10,
        'Restaurants': 10,
        'Shopping': 10,
    }
    
    if thresholds:
        default_thresholds.update(thresholds)
    
    alerts = []
    
    for category, data in distribution.items():
        pct_of_income = data['percentage_of_income']
        
        # Find applicable threshold
        threshold = None
        for threshold_category, threshold_value in default_thresholds.items():
            if category.lower() == threshold_category.lower():
                threshold = threshold_value
                break
        
        # Use generic threshold if no specific match
        if threshold is None:
            threshold = 5  # Generic category threshold
        
        # Generate alert if exceeded
        if pct_of_income > threshold:
            amount = data['total_spent']
            recommendation = monthly_income * (threshold / 100)
            overage = amount - recommendation
            
            alerts.append({
                'category': category,
                'current_percentage': pct_of_income,
                'recommended_percentage': threshold,
                'current_amount': amount,
                'recommended_amount': _round_currency(recommendation),
                'overage_amount': _round_currency(overage),
                'severity': _calculate_severity(pct_of_income, threshold),
                'message': f"{category} spending ({pct_of_income:.1f}%) exceeds "
                          f"recommended {threshold:.1f}% threshold. "
                          f"Consider reducing by ${overage:,.2f}/month."
            })
    
    return alerts


def detect_recurring_subscription_charges(
    transactions: List[Transaction],
    min_occurrences: int = 2
) -> List[Dict[str, any]]:
    """Detect recurring subscription charges.
    
    Identifies transactions that appear to be recurring based on:
    1. Same merchant, same amount, roughly monthly intervals
    2. Flagged as recurring in transaction data
    3. Regular pattern (e.g., same day each month)
    
    Args:
        transactions: List of Transaction objects
        min_occurrences: Minimum occurrences to consider recurring (default 2)
        
    Returns:
        List of detected subscriptions:
        [
            {
                'merchant_name': str,
                'amount': float,
                'frequency': str,  # MONTHLY, WEEKLY, DAILY
                'last_charge': date,
                'next_estimated_charge': date,
                'monthly_cost': float,
                'yearly_cost': float,
                'transaction_count': int,
                'flagged_as_recurring': bool,
            }
        ]
    """
    if not transactions:
        return []
    
    # Filter to expense transactions with merchants
    expense_txns = [
        t for t in transactions
        if t.transaction_type == 'EXPENSE' and t.merchant_name
    ]
    
    # Group by merchant and amount
    merchant_patterns = {}
    
    for txn in expense_txns:
        key = (txn.merchant_name, float(txn.amount))
        if key not in merchant_patterns:
            merchant_patterns[key] = []
        merchant_patterns[key].append(txn)
    
    subscriptions = []
    
    for (merchant, amount), txns in merchant_patterns.items():
        # Only consider if recurring or multiple occurrences
        if len(txns) < min_occurrences and not any(t.is_recurring for t in txns):
            continue
        
        # Sort by date
        txns = sorted(txns, key=lambda t: t.transaction_date)
        
        # Calculate frequency
        if len(txns) >= 2:
            intervals = []
            for i in range(1, len(txns)):
                delta = (txns[i].transaction_date - txns[i-1].transaction_date).days
                intervals.append(delta)
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 30
            
            # Determine frequency
            if 6 <= avg_interval <= 8:
                frequency = 'WEEKLY'
                multiplier = 52
            elif 28 <= avg_interval <= 35:
                frequency = 'MONTHLY'
                multiplier = 12
            elif 88 <= avg_interval <= 95:
                frequency = 'QUARTERLY'
                multiplier = 4
            elif 355 <= avg_interval <= 370:
                frequency = 'ANNUAL'
                multiplier = 1
            else:
                frequency = f'EVERY_{int(avg_interval)}_DAYS'
                multiplier = 365 / avg_interval
        else:
            frequency = 'MONTHLY'  # Assume monthly if only 1 occurrence
            multiplier = 12
        
        last_txn = txns[-1]
        
        # Estimate next charge
        if frequency == 'WEEKLY':
            next_estimated = last_txn.transaction_date + timedelta(days=7)
        elif frequency == 'MONTHLY':
            # Add 30 days as approximation
            next_estimated = last_txn.transaction_date + timedelta(days=30)
        elif frequency == 'QUARTERLY':
            next_estimated = last_txn.transaction_date + timedelta(days=90)
        elif frequency == 'ANNUAL':
            next_estimated = last_txn.transaction_date + timedelta(days=365)
        else:
            next_estimated = last_txn.transaction_date + timedelta(days=avg_interval)
        
        subscriptions.append({
            'merchant_name': merchant,
            'amount': _round_currency(amount),
            'frequency': frequency,
            'last_charge': last_txn.transaction_date,
            'next_estimated_charge': next_estimated,
            'monthly_cost': _round_currency(amount * (multiplier / 12)),
            'yearly_cost': _round_currency(amount * multiplier),
            'transaction_count': len(txns),
            'flagged_as_recurring': any(t.is_recurring for t in txns),
        })
    
    return sorted(subscriptions, key=lambda x: x['yearly_cost'], reverse=True)


def generate_spending_recommendations(
    distribution: Dict[str, Dict[str, float]],
    alerts: List[Dict[str, str]],
    subscriptions: List[Dict[str, any]],
    budget_ratio: float
) -> List[str]:
    """Generate actionable spending recommendations.
    
    Args:
        distribution: Category distribution
        alerts: High spending alerts
        subscriptions: Detected subscriptions
        budget_ratio: Overall budget ratio
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Budget ratio recommendations
    if budget_ratio > 0.9:
        recommendations.append(
            "Your spending is very close to (or exceeds) your income. "
            "Consider increasing income or reducing expenses urgently."
        )
    elif budget_ratio > 0.7:
        recommendations.append(
            "You have limited financial flexibility. Focus on essential expenses "
            "and eliminate non-essential spending."
        )
    elif budget_ratio > 0.5:
        recommendations.append(
            "Consider increasing your savings rate. Review discretionary spending "
            "for reduction opportunities."
        )
    
    # Category-based recommendations
    if alerts:
        top_alert = alerts[0]
        recommendations.append(
            f"Your {top_alert['category']} spending is {top_alert['overage_amount']} "
            f"over target. Implement a reduction strategy."
        )
    
    # Subscription recommendations
    total_subscription_yearly = sum(s['yearly_cost'] for s in subscriptions)
    if total_subscription_yearly > 1000:  # Over $1000/year in subscriptions
        recommendations.append(
            f"Annual subscription costs total ${total_subscription_yearly:,.2f}. "
            f"Review all subscriptions and eliminate unused services."
        )
    
    if len(subscriptions) > 5:
        recommendations.append(
            f"You have {len(subscriptions)} detected subscriptions. "
            f"Consolidate or cancel duplicate/redundant services."
        )
    
    return recommendations


def _calculate_severity(actual_pct: float, threshold_pct: float) -> str:
    """Calculate severity level based on overage amount.
    
    Args:
        actual_pct: Actual percentage
        threshold_pct: Threshold percentage
        
    Returns:
        'LOW', 'MEDIUM', or 'HIGH'
    """
    overage_ratio = (actual_pct - threshold_pct) / threshold_pct
    
    if overage_ratio <= 0.1:
        return 'LOW'
    elif overage_ratio <= 0.25:
        return 'MEDIUM'
    else:
        return 'HIGH'
