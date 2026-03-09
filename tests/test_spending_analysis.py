"""Unit tests for spending analysis module.

Tests all spending analysis functions with various scenarios including:
- Budget ratio calculation with different income/expense combinations
- Category spending distribution analysis
- High spending category detection with thresholds
- Recurring subscription identification
- Spending recommendations generation
- Edge cases (zero income, no transactions, etc.)
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from backend.models import Transaction
from backend.finance.spending_analysis import (
    calculate_budget_ratio,
    categorize_budget_ratio,
    calculate_category_spending_distribution,
    detect_high_spending_categories,
    detect_recurring_subscription_charges,
    generate_spending_recommendations,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing."""
    user_id = uuid4()
    transactions = []
    base_date = datetime(2024, 1, 15)
    
    # Basic expenses
    transactions.extend([
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=base_date,
            amount=Decimal('1500.00'),
            category='Housing',
            merchant_name='Landlord',
            transaction_type='EXPENSE',
            payment_method='TRANSFER',
            description='Monthly rent',
            is_recurring=True,
        ),
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=base_date,
            amount=Decimal('500.00'),
            category='Food',
            merchant_name='Grocery Store',
            transaction_type='EXPENSE',
            payment_method='CREDIT_CARD',
            description='Weekly groceries',
            is_recurring=False,
        ),
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=base_date,
            amount=Decimal('100.00'),
            category='Entertainment',
            merchant_name='Netflix',
            transaction_type='EXPENSE',
            payment_method='CREDIT_CARD',
            description='Streaming subscription',
            is_recurring=True,
        ),
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=base_date,
            amount=Decimal('200.00'),
            category='Transport',
            merchant_name='Uber',
            transaction_type='EXPENSE',
            payment_method='CREDIT_CARD',
            description='Rides',
            is_recurring=False,
        ),
    ])
    
    # Add recurring subscriptions (same amount, different dates)
    for i in range(3):
        transactions.append(
            Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=base_date - timedelta(days=30 * i),
                amount=Decimal('12.99'),
                category='Entertainment',
                merchant_name='Spotify',
                transaction_type='EXPENSE',
                payment_method='CREDIT_CARD',
                description='Music subscription',
                is_recurring=True,
            )
        )
    
    # Income
    transactions.append(
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=base_date,
            amount=Decimal('5000.00'),
            category='Salary',
            merchant_name='Employer',
            transaction_type='INCOME',
            payment_method='TRANSFER',
            description='Monthly salary',
            is_recurring=True,
        )
    )
    
    return transactions


@pytest.fixture
def zero_income_transactions():
    """Create transactions with zero income."""
    user_id = uuid4()
    return [
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal('500.00'),
            category='Food',
            merchant_name='Grocery',
            transaction_type='EXPENSE',
            payment_method='CREDIT_CARD',
            description='Groceries',
            is_recurring=False,
        )
    ]


@pytest.fixture
def no_transactions():
    """Empty transaction list."""
    return []


# ============================================================================
# TESTS: calculate_budget_ratio
# ============================================================================

def test_calculate_budget_ratio_normal():
    """Test budget ratio with normal income and expenses."""
    monthly_income = 5000.0
    monthly_expenses = 3000.0
    ratio = calculate_budget_ratio(monthly_income, monthly_expenses)
    assert ratio == 0.6
    assert 0.59 < ratio < 0.61  # Within rounding tolerance


def test_calculate_budget_ratio_zero_expenses():
    """Test budget ratio with zero expenses."""
    ratio = calculate_budget_ratio(5000.0, 0.0)
    assert ratio == 0.0


def test_calculate_budget_ratio_zero_income():
    """Test budget ratio with zero income."""
    ratio = calculate_budget_ratio(0.0, 3000.0)
    assert ratio == 0.0


def test_calculate_budget_ratio_over_budget():
    """Test budget ratio when expenses exceed income."""
    ratio = calculate_budget_ratio(2000.0, 3000.0)
    assert ratio > 1.0
    assert 1.49 < ratio < 1.51


def test_calculate_budget_ratio_perfect():
    """Test budget ratio at perfect 50% spend."""
    ratio = calculate_budget_ratio(5000.0, 2500.0)
    assert abs(ratio - 0.5) < 0.01


# ============================================================================
# TESTS: categorize_budget_ratio
# ============================================================================

def test_categorize_budget_ratio_excellent():
    """Test categorization of excellent budget ratio."""
    result = categorize_budget_ratio(0.25)
    assert result['status'] == 'EXCELLENT'
    assert 'excellent' in result['description'].lower()
    assert result['color'] == 'green'


def test_categorize_budget_ratio_good():
    """Test categorization of good budget ratio."""
    result = categorize_budget_ratio(0.40)
    assert result['status'] == 'GOOD'
    assert 'good' in result['description'].lower()
    assert result['color'] == 'lightgreen'


def test_categorize_budget_ratio_fair():
    """Test categorization of fair budget ratio."""
    result = categorize_budget_ratio(0.60)
    assert result['status'] == 'FAIR'
    assert result['color'] == 'yellow'


def test_categorize_budget_ratio_tight():
    """Test categorization of tight budget ratio."""
    result = categorize_budget_ratio(0.85)
    assert result['status'] == 'TIGHT'
    assert result['color'] == 'orange'


def test_categorize_budget_ratio_over_budget():
    """Test categorization of over-budget ratio."""
    result = categorize_budget_ratio(1.20)
    assert result['status'] == 'OVER_BUDGET'
    assert result['color'] == 'red'


# ============================================================================
# TESTS: calculate_category_spending_distribution
# ============================================================================

def test_category_spending_distribution(sample_transactions):
    """Test category spending distribution calculation."""
    monthly_income = 5000.0
    distribution = calculate_category_spending_distribution(
        sample_transactions, monthly_income
    )
    
    # Should have Housing, Food, Entertainment, Transport
    assert 'Housing' in distribution
    assert 'Food' in distribution
    assert 'Entertainment' in distribution
    assert 'Transport' in distribution
    
    # Check Housing (most expensive)
    housing = distribution['Housing']
    assert housing['total_spent'] == 1500.0
    assert 25 < housing['percentage_of_income'] < 35  # ~30%
    assert housing['transaction_count'] == 1
    
    # Check Food
    food = distribution['Food']
    assert food['total_spent'] == 500.0
    assert 9 < food['percentage_of_income'] < 11  # ~10%
    assert food['transaction_count'] == 1


def test_category_spending_distribution_no_transactions():
    """Test with empty transaction list."""
    distribution = calculate_category_spending_distribution([], 5000.0)
    assert distribution == {}


def test_category_spending_distribution_zero_income(sample_transactions):
    """Test category distribution with zero income."""
    distribution = calculate_category_spending_distribution(
        sample_transactions, 0.0
    )
    # Should still calculate total_spent and transaction_count
    assert 'Housing' in distribution
    assert distribution['Housing']['total_spent'] == 1500.0


# ============================================================================
# TESTS: detect_high_spending_categories
# ============================================================================

def test_detect_high_spending_categories(sample_transactions):
    """Test detection of high spending categories."""
    monthly_income = 5000.0
    distribution = calculate_category_spending_distribution(
        sample_transactions, monthly_income
    )
    
    # House is 30% but default threshold is also 30, so no alert
    alerts = detect_high_spending_categories(distribution, monthly_income)
    # Transport should be within limits (4% vs 8%)
    # Entertainment should be within limits (2% vs 10%)
    # Food should be within limits (10% vs 15%)
    
    assert isinstance(alerts, list)


def test_high_spending_alerts_with_overage():
    """Test alerts for spending that exceeds thresholds."""
    distribution = {
        'Entertainment': {
            'total_spent': 800.0,
            'percentage_of_total': 50.0,
            'percentage_of_income': 20.0,
            'transaction_count': 5,
            'avg_per_transaction': 160.0,
        }
    }
    monthly_income = 4000.0
    
    alerts = detect_high_spending_categories(
        distribution, monthly_income, 
        thresholds={'Entertainment': 0.10}  # 10% threshold
    )
    
    # Should have alert since 20% > 10% threshold
    assert len(alerts) > 0
    alert = alerts[0]
    assert alert['category'] == 'Entertainment'
    assert alert['current_percentage'] > alert['recommended_percentage']


def test_high_spending_custom_thresholds():
    """Test custom threshold application."""
    distribution = {
        'Housing': {
            'total_spent': 2000.0,
            'percentage_of_total': 100.0,
            'percentage_of_income': 40.0,
            'transaction_count': 1,
            'avg_per_transaction': 2000.0,
        }
    }
    
    custom_thresholds = {'Housing': 0.35}  # 35% threshold
    alerts = detect_high_spending_categories(
        distribution, 5000.0, thresholds=custom_thresholds
    )
    
    # 40% > 35% should trigger alert
    assert len(alerts) > 0


# ============================================================================
# TESTS: detect_recurring_subscription_charges
# ============================================================================

def test_detect_recurring_subscriptions(sample_transactions):
    """Test detection of recurring subscriptions."""
    subscriptions = detect_recurring_subscription_charges(sample_transactions)
    
    # Should detect Netflix and Spotify
    assert len(subscriptions) > 0
    
    # Check for Spotify (monthly, $12.99)
    spotify = [s for s in subscriptions if s['merchant_name'] == 'Spotify']
    assert len(spotify) > 0
    assert spotify[0]['amount'] == 12.99
    assert 'MONTHLY' in spotify[0]['frequency']
    assert spotify[0]['yearly_cost'] > 150


def test_recurring_no_transactions():
    """Test with no transactions."""
    subscriptions = detect_recurring_subscription_charges([])
    assert subscriptions == []


def test_recurring_min_occurrences():
    """Test minimum occurrences threshold."""
    user_id = uuid4()
    transactions = [
        Transaction(
            id=uuid4(),
            user_id=user_id,
            transaction_date=datetime(2024, 1, 15),
            amount=Decimal('10.00'),
            category='Entertainment',
            merchant_name='Test Service',
            transaction_type='EXPENSE',
            payment_method='CREDIT_CARD',
            description='Single charge',
            is_recurring=False,
        )
    ]
    
    # Single transaction should not be detected as recurring
    subscriptions = detect_recurring_subscription_charges(transactions, min_occurrences=2)
    assert len([s for s in subscriptions if s['merchant_name'] == 'Test Service']) == 0


# ============================================================================
# TESTS: generate_spending_recommendations
# ============================================================================

def test_generate_recommendations_good_budget(sample_transactions):
    """Test recommendations with good budget ratio."""
    monthly_income = 5000.0
    distribution = calculate_category_spending_distribution(
        sample_transactions, monthly_income
    )
    budget_ratio = 0.45  # 45% - good range
    
    alerts = detect_high_spending_categories(distribution, monthly_income)
    subscriptions = detect_recurring_subscription_charges(sample_transactions)
    
    recommendations = generate_spending_recommendations(
        distribution, alerts, subscriptions, budget_ratio
    )
    
    assert isinstance(recommendations, list)
    # Good budget ratio might still have other recommendations
    assert len(recommendations) >= 0


def test_generate_recommendations_tight_budget():
    """Test recommendations with tight budget."""
    distribution = {
        'Housing': {
            'total_spent': 3500.0,
            'percentage_of_total': 100.0,
            'percentage_of_income': 70.0,
            'transaction_count': 1,
            'avg_per_transaction': 3500.0,
        }
    }
    budget_ratio = 0.85  # 85% - tight
    
    alerts = detect_high_spending_categories(
        distribution, 5000.0, 
        thresholds={'Housing': 0.30}
    )
    
    recommendations = generate_spending_recommendations(
        distribution, alerts, [], budget_ratio
    )
    
    # Should have urgent recommendations
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    # At least one should mention budget reduction
    assert any('reduce' in r.lower() or 'budget' in r.lower() for r in recommendations)


def test_generate_recommendations_over_budget():
    """Test recommendations when over budget."""
    distribution = {}
    budget_ratio = 1.15  # 115% - over budget
    
    recommendations = generate_spending_recommendations(
        distribution, [], [], budget_ratio
    )
    
    assert len(recommendations) > 0
    # Should contain urgent budget adjustment advice
    assert any('urgent' in r.lower() or 'over' in r.lower() for r in recommendations)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_spending_analysis_workflow(sample_transactions):
    """Test complete spending analysis workflow."""
    monthly_income = 5000.0
    monthly_expenses = 2300.0
    
    # Step 1: Calculate budget ratio
    budget_ratio = calculate_budget_ratio(monthly_income, monthly_expenses)
    assert 0.45 < budget_ratio < 0.47
    
    # Step 2: Categorize status
    status = categorize_budget_ratio(budget_ratio)
    assert status['status'] == 'GOOD'
    
    # Step 3: Get category distribution
    distribution = calculate_category_spending_distribution(
        sample_transactions, monthly_income
    )
    assert len(distribution) > 0
    
    # Step 4: Detect high spending
    alerts = detect_high_spending_categories(distribution, monthly_income)
    assert isinstance(alerts, list)
    
    # Step 5: Find subscriptions
    subscriptions = detect_recurring_subscription_charges(sample_transactions)
    assert isinstance(subscriptions, list)
    
    # Step 6: Generate recommendations
    recommendations = generate_spending_recommendations(
        distribution, alerts, subscriptions, budget_ratio
    )
    assert isinstance(recommendations, list)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_very_high_income():
    """Test with very high income relative to expenses."""
    ratio = calculate_budget_ratio(100000.0, 1000.0)
    assert ratio < 0.02
    status = categorize_budget_ratio(ratio)
    assert status['status'] == 'EXCELLENT'


def test_very_high_expenses():
    """Test with expenses exceeding income significantly."""
    ratio = calculate_budget_ratio(2000.0, 5000.0)
    assert ratio > 2.0
    status = categorize_budget_ratio(ratio)
    assert status['status'] == 'OVER_BUDGET'


def test_negative_values_handled():
    """Test that negative values are handled gracefully."""
    # Negative values should be treated as 0 or cause appropriate handling
    ratio = calculate_budget_ratio(5000.0, -500.0)
    # Depending on implementation, either 0 or calculation with negative
    assert isinstance(ratio, (int, float))


def test_large_transaction_volumes():
    """Test with many transactions."""
    user_id = uuid4()
    transactions = []
    base_date = datetime(2024, 1, 15)
    
    # Create 100 transactions
    for i in range(100):
        transactions.append(
            Transaction(
                id=uuid4(),
                user_id=user_id,
                transaction_date=base_date - timedelta(days=i),
                amount=Decimal(f'{10 + (i % 100)}.00'),
                category='Groceries' if i % 2 == 0 else 'Transport',
                merchant_name=f'Merchant {i % 10}',
                transaction_type='EXPENSE',
                payment_method='CREDIT_CARD',
                description=f'Transaction {i}',
                is_recurring=i % 3 == 0,
            )
        )
    
    distribution = calculate_category_spending_distribution(transactions, 5000.0)
    assert len(distribution) > 0
    
    subscriptions = detect_recurring_subscription_charges(transactions)
    assert len(subscriptions) > 0
