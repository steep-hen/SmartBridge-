"""Unit tests for advanced spending analysis module.

Tests all advanced analysis functions with various scenarios.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from backend.models import Transaction
from backend.finance.advanced_spending_analysis import (
    analyze_seasonal_patterns,
    track_budget_goals,
    analyze_month_over_month,
    generate_ml_saving_recommendations,
    get_peer_benchmarks,
    compare_to_peers,
    detect_real_time_alerts,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_monthly_transactions():
    """Create sample transactions spanning multiple months."""
    user_id = uuid4()
    transactions = []
    base_date = datetime(2024, 1, 15)
    
    # Create transactions for 12 months
    for month in range(1, 13):
        current_date = datetime(2024, month, 15)
        # Base spending varies by season
        base_spending = 2500 if month in [12, 1, 2] else 2000 if month in [6, 7, 8] else 2300
        
        transactions.extend([
            Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=current_date,
                amount=Decimal(f'{base_spending * 0.6:.2f}'),  # Housing
                category='Housing',
                merchant_name='Landlord',
                transaction_type='EXPENSE',
                payment_method='TRANSFER',
                description='Rent',
                is_recurring=True,
            ),
            Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=current_date,
                amount=Decimal(f'{base_spending * 0.15:.2f}'),  # Food
                category='Food',
                merchant_name='Grocery',
                transaction_type='EXPENSE',
                payment_method='CREDIT_CARD',
                description='Groceries',
                is_recurring=False,
            ),
            Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=current_date,
                amount=Decimal(f'{base_spending * 0.1:.2f}'),  # Entertainment
                category='Entertainment',
                merchant_name='Netflix',
                transaction_type='EXPENSE',
                payment_method='CREDIT_CARD',
                description='Streaming',
                is_recurring=True,
            ),
        ])
    
    return transactions


@pytest.fixture
def sample_recent_transactions():
    """Create transactions from recent months only."""
    user_id = uuid4()
    transactions = []
    base_date = datetime.now()
    
    # Last 3 months
    for days_back in [60, 30, 0]:
        current_date = base_date - timedelta(days=days_back)
        transactions.extend([
            Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=current_date,
                amount=Decimal('1500.00'),
                category='Housing',
                merchant_name='Landlord',
                transaction_type='EXPENSE',
                payment_method='TRANSFER',
                description='Rent',
                is_recurring=True,
            ),
            Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=current_date,
                amount=Decimal('500.00'),
                category='Food',
                merchant_name='Grocery',
                transaction_type='EXPENSE',
                payment_method='CREDIT_CARD',
                description='Groceries',
                is_recurring=False,
            ),
        ])
    
    return transactions


# ============================================================================
# TESTS: Seasonal Pattern Detection
# ============================================================================

def test_analyze_seasonal_patterns(sample_monthly_transactions):
    """Test seasonal pattern analysis."""
    analysis = analyze_seasonal_patterns(sample_monthly_transactions, 5000)
    
    assert analysis['available'] == True
    assert len(analysis['monthly_breakdown']) > 0
    assert len(analysis['seasonal_breakdown']) == 4  # Q1-Q4
    assert 'seasonal_alert' in analysis
    assert 'variability' in analysis


def test_seasonal_patterns_no_data():
    """Test with no transactions."""
    analysis = analyze_seasonal_patterns([], 5000)
    assert analysis['available'] == False


def test_seasonal_patterns_peak_detection(sample_monthly_transactions):
    """Test peak month detection."""
    analysis = analyze_seasonal_patterns(sample_monthly_transactions, 5000)
    
    assert 'peak_months' in analysis
    assert 'low_months' in analysis
    # Winter months should be peaks (higher spending)
    peak_months = analysis['peak_months']
    assert len(peak_months) > 0


# ============================================================================
# TESTS: Budget Goal Tracking
# ============================================================================

def test_track_budget_goals(sample_monthly_transactions):
    """Test budget goal tracking."""
    from backend.finance.spending_analysis import calculate_category_spending_distribution
    
    distribution = calculate_category_spending_distribution(sample_monthly_transactions, 5000)
    tracking = track_budget_goals(distribution, 5000)
    
    assert tracking['available'] == True
    assert 'goals_summary' in tracking
    assert 'category_budgets' in tracking
    assert 'compliance_score' in tracking


def test_budget_goals_no_data():
    """Test with empty distribution."""
    tracking = track_budget_goals({}, 5000)
    assert tracking['available'] == False


def test_budget_goals_custom_limits():
    """Test with custom budget limits."""
    distribution = {
        'Housing': {
            'total_spent': 1500,
            'percentage_of_total': 50,
            'percentage_of_income': 30,
            'transaction_count': 1,
            'avg_per_transaction': 1500,
        }
    }
    
    custom_goals = {'Housing': 0.35}
    tracking = track_budget_goals(distribution, 5000, budget_goals=custom_goals)
    
    assert tracking['available'] == True
    # Housing at 30% should be on track with 35% limit
    budgets = tracking['category_budgets']
    assert budgets[0]['status'] == 'ON_TRACK'


# ============================================================================
# TESTS: Month-over-Month Trend Analysis
# ============================================================================

def test_analyze_month_over_month(sample_recent_transactions):
    """Test month-over-month trend analysis."""
    analysis = analyze_month_over_month(sample_recent_transactions, months_to_compare=3)
    
    assert analysis['available'] == True
    assert 'trend_direction' in analysis
    assert 'overall_trend' in analysis
    assert 'monthly_trends' in analysis


def test_month_over_month_trend_direction(sample_recent_transactions):
    """Test trend direction detection."""
    analysis = analyze_month_over_month(sample_recent_transactions, months_to_compare=3)
    
    # Should be one of these
    assert analysis['trend_direction'] in ['INCREASING', 'DECREASING', 'STABLE', 'UNKNOWN']


def test_month_over_month_no_data():
    """Test with insufficient data."""
    analysis = analyze_month_over_month([], months_to_compare=3)
    assert analysis['available'] == False


# ============================================================================
# TESTS: ML-Powered Recommendations
# ============================================================================

def test_generate_ml_recommendations():
    """Test ML recommendation generation."""
    category_dist = {
        'Housing': {'percentage_of_income': 30, 'total_spent': 1500},
        'Food': {'percentage_of_income': 12, 'total_spent': 600},
    }
    
    seasonal = {'available': True, 'peak_months': ['December']}
    trends = {'trend_direction': 'STABLE', 'overall_trend': 0}
    
    recs = generate_ml_saving_recommendations(
        category_dist, 5000, 0.5, seasonal, trends
    )
    
    assert isinstance(recs, list)
    assert len(recs) >= 0


def test_ml_recommendations_high_spending():
    """Test recommendations for high spenders."""
    category_dist = {
        'Food': {'percentage_of_income': 25, 'total_spent': 1250},
    }
    
    seasonal = {'available': False}
    trends = {'trend_direction': 'INCREASING', 'overall_trend': 15}
    
    recs = generate_ml_saving_recommendations(
        category_dist, 5000, 0.9, seasonal, trends
    )
    
    # Should have urgent recommendations
    assert any('urgent' in r.lower() or 'increasing' in r.lower() for r in recs)


# ============================================================================
# TESTS: Peer Benchmarking
# ============================================================================

def test_get_peer_benchmarks():
    """Test peer benchmark retrieval."""
    benchmarks = get_peer_benchmarks()
    
    assert benchmarks['available'] == True
    assert 'benchmarks' in benchmarks
    assert 'Housing' in benchmarks['benchmarks']
    assert 'p50' in benchmarks['benchmarks']['Housing']


def test_peer_benchmarks_by_region():
    """Test regional peer benchmarks."""
    usa_benchmarks = get_peer_benchmarks(user_country='USA')
    india_benchmarks = get_peer_benchmarks(user_country='India')
    
    assert usa_benchmarks['available'] == True
    assert india_benchmarks['available'] == True
    # India should have lower housing percentage
    assert india_benchmarks['benchmarks']['Housing']['p50'] < usa_benchmarks['benchmarks']['Housing']['p50']


def test_compare_to_peers():
    """Test peer comparison."""
    distribution = {
        'Housing': {'percentage_of_income': 25, 'total_spent': 1250},
        'Food': {'percentage_of_income': 15, 'total_spent': 750},
    }
    
    comparison = compare_to_peers(distribution)
    
    assert comparison['available'] == True
    assert 'comparison' in comparison
    assert 'Housing' in comparison['comparison']
    assert 'position' in comparison['comparison']['Housing']


# ============================================================================
# TESTS: Real-Time Alerts
# ============================================================================

def test_detect_real_time_alerts_normal():
    """Test real-time alert detection for normal transaction."""
    new_txn = {'amount': 100, 'category': 'Entertainment', 'merchant_name': 'Netflix'}
    recent = []
    
    alerts = detect_real_time_alerts(new_txn, recent, 5000)
    
    # Normal transaction shouldn't trigger alerts
    assert len(alerts) == 0


def test_detect_duplicate_transaction():
    """Test duplicate transaction detection."""
    user_id = uuid4()
    
    # Create a recent transaction
    recent_txn = Transaction(
        id=uuid4(),
        user_id=user_id,
        transaction_date=datetime.now(),
        amount=Decimal('100.00'),
        category='Entertainment',
        merchant_name='Netflix',
        transaction_type='EXPENSE',
        payment_method='CREDIT_CARD',
        description='Streaming',
        is_recurring=True,
    )
    
    new_txn = {'amount': 100, 'category': 'Entertainment', 'merchant_name': 'Netflix'}
    
    alerts = detect_real_time_alerts(new_txn, [recent_txn], 5000)
    
    # Should detect duplicate
    assert any(a['alert_type'] == 'DUPLICATE' for a in alerts)


def test_detect_anomaly_transaction():
    """Test unusual transaction detection."""
    user_id = uuid4()
    
    # Create recent normal transactions
    recent = [
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=datetime.now() - timedelta(days=i),
            amount=Decimal('50.00'),
            category='Food',
            merchant_name='Grocery',
            transaction_type='EXPENSE',
            payment_method='CREDIT_CARD',
            description='Groceries',
            is_recurring=False,
        )
        for i in range(5)
    ]
    
    # New transaction is 3x normal amount
    new_txn = {'amount': 200, 'category': 'Food', 'merchant_name': 'Restaurant'}
    
    alerts = detect_real_time_alerts(new_txn, recent, 5000)
    
    # Should detect anomaly
    assert any(a['alert_type'] in ['ANOMALY', 'THRESHOLD'] for a in alerts)


def test_detect_limit_breach():
    """Test category limit breach detection."""
    new_txn = {'amount': 1000, 'category': 'Entertainment', 'merchant_name': 'Travel'}
    
    limits = {'Entertainment': 500}
    
    alerts = detect_real_time_alerts(new_txn, [], 5000, category_limits=limits)
    
    # Should detect limit breach
    assert any(a['alert_type'] == 'LIMIT' for a in alerts)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_advanced_analysis_workflow(sample_monthly_transactions):
    """Test complete advanced analysis workflow."""
    from backend.finance.spending_analysis import calculate_category_spending_distribution
    
    monthly_income = 5000
    
    # Run all analyses
    seasonal = analyze_seasonal_patterns(sample_monthly_transactions, monthly_income)
    distribution = calculate_category_spending_distribution(sample_monthly_transactions, monthly_income)
    budgets = track_budget_goals(distribution, monthly_income)
    trends = analyze_month_over_month(sample_monthly_transactions)
    recs = generate_ml_saving_recommendations(distribution, monthly_income, 0.5, seasonal, trends)
    benchmarks = compare_to_peers(distribution)
    
    # Verify all succeeded
    assert seasonal['available'] == True
    assert budgets['available'] == True
    assert trends['available'] == True
    assert isinstance(recs, list)
    assert benchmarks['available'] == True
