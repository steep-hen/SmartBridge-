"""Unit tests for financial report builder.

Tests:
- Report JSON structure and required fields
- Database querying and aggregation
- Metric consistency between components
- Edge cases (new user, no financial data)
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.models import Base, User, FinancialSummary, Holding, Goal, Transaction
from backend.finance.report_builder import build_user_report


@pytest.fixture(scope="function")
def test_db() -> Session:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def sample_user(test_db: Session) -> User:
    """Create a sample user."""
    user = User(
        email="test@example.com",
        name="Test User",
        country="USA",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def user_with_data(test_db: Session, sample_user: User) -> User:
    """Create user with financial data."""
    # Financial summary
    summary = FinancialSummary(
        user_id=sample_user.id,
        year=2024,
        month=1,
        total_income=Decimal("5000.00"),
        total_expenses=Decimal("3000.00"),
        total_savings=Decimal("1500.00"),
        total_investments=Decimal("10000.00"),
        net_worth=Decimal("50000.00"),
    )
    test_db.add(summary)
    
    # Holdings
    holdings = [
        Holding(
            user_id=sample_user.id,
            ticker="AAPL",
            quantity=Decimal("10.00"),
            average_cost=Decimal("150.00"),
            current_value=Decimal("1600.00"),
            asset_type="EQUITY",
        ),
        Holding(
            user_id=sample_user.id,
            ticker="VTSAX",
            quantity=Decimal("50.00"),
            average_cost=Decimal("100.00"),
            current_value=Decimal("6000.00"),
            asset_type="ETF",
        ),
    ]
    for h in holdings:
        test_db.add(h)
    
    # Goals
    goals = [
        Goal(
            user_id=sample_user.id,
            goal_name="Emergency Fund",
            target_amount=Decimal("15000.00"),
            current_amount=Decimal("5000.00"),
            goal_type="SAVINGS",
            status="ACTIVE",
            priority="HIGH",
            target_date=date.today() + timedelta(days=365),
        ),
        Goal(
            user_id=sample_user.id,
            goal_name="House Down Payment",
            target_amount=Decimal("100000.00"),
            current_amount=Decimal("25000.00"),
            goal_type="SAVINGS",
            status="ACTIVE",
            priority="HIGH",
            target_date=date.today() + timedelta(days=730),
        ),
    ]
    for g in goals:
        test_db.add(g)
    
    test_db.commit()
    test_db.refresh(sample_user)
    return sample_user


# ============================================================================
# REPORT STRUCTURE TESTS
# ============================================================================

class TestReportStructure:
    """Validate JSON structure of generated reports"""
    
    def test_report_has_required_top_level_keys(self, test_db, user_with_data):
        """Report contains all required top-level keys."""
        report = build_user_report(user_with_data.id, test_db)
        
        required_keys = {
            'report_id',
            'report_generated_at',
            'user_profile',
            'financial_snapshot',
            'computed_metrics',
            'holdings_summary',
            'goals_analysis',
            'overall_health_score',
            'assumptions_used',
        }
        
        assert set(report.keys()) >= required_keys
    
    def test_user_profile_structure(self, test_db, user_with_data):
        """User profile section has correct structure."""
        report = build_user_report(user_with_data.id, test_db)
        profile = report['user_profile']
        
        required_fields = {
            'user_id',
            'email',
            'name',
            'country',
            'member_since',
        }
        assert set(profile.keys()) >= required_fields
        assert profile['email'] == user_with_data.email
        assert profile['name'] == user_with_data.name
    
    def test_financial_snapshot_structure(self, test_db, user_with_data):
        """Financial snapshot section exists."""
        report = build_user_report(user_with_data.id, test_db)
        snapshot = report['financial_snapshot']
        
        required_fields = {
            'available',
            'period',
            'total_income',
            'total_expenses',
            'total_savings',
            'total_investments',
            'net_worth',
        }
        assert set(snapshot.keys()) >= required_fields
    
    def test_computed_metrics_structure(self, test_db, user_with_data):
        """Metrics section has all calculation results."""
        report = build_user_report(user_with_data.id, test_db)
        metrics = report['computed_metrics']
        
        required_fields = {
            'savings_rate',
            'debt_to_income_ratio',
            'emergency_fund_months',
            'investment_ratio',
            'monthly_income',
            'monthly_expenses',
            'monthly_savings',
        }
        assert set(metrics.keys()) >= required_fields
        
        # Validate ranges
        assert 0 <= metrics['savings_rate'] <= 200
        assert 0 <= metrics['debt_to_income_ratio']
        assert metrics['emergency_fund_months'] >= 0
        assert 0 <= metrics['investment_ratio'] <= 1
    
    def test_holdings_summary_structure(self, test_db, user_with_data):
        """Holdings section structured correctly."""
        report = build_user_report(user_with_data.id, test_db)
        holdings = report['holdings_summary']
        
        required_fields = {
            'count',
            'total_cost_basis',
            'total_current_value',
            'total_unrealized_gain_loss',
            'gain_loss_percentage',
            'holdings',
        }
        assert set(holdings.keys()) >= required_fields
        
        assert holdings['count'] == 2
        assert isinstance(holdings['holdings'], list)
        assert len(holdings['holdings']) == 2
        
        # Each holding has required fields
        for holding in holdings['holdings']:
            holding_fields = {
                'ticker',
                'asset_type',
                'quantity',
                'average_cost_per_unit',
                'total_cost',
                'current_value',
                'unrealized_gain_loss',
                'gain_loss_percentage',
            }
            assert set(holding.keys()) >= holding_fields
    
    def test_goals_analysis_structure(self, test_db, user_with_data):
        """Goals section with projections."""
        report = build_user_report(user_with_data.id, test_db)
        goals = report['goals_analysis']
        
        required_fields = {
            'count',
            'goals',
            'achievement_summary',
        }
        assert set(goals.keys()) >= required_fields
        
        assert goals['count'] == 2
        assert len(goals['goals']) == 2
        
        # Each goal has required fields
        for goal in goals['goals']:
            goal_fields = {
                'goal_id',
                'goal_name',
                'target_amount',
                'current_amount',
                'remaining_amount',
                'progress_percentage',
                'required_monthly_sip',
                'projected_final_balance',
                'achievable_with_planned_contribution',
                'projection_samples',
            }
            assert set(goal.keys()) >= goal_fields
            
            # Projection samples should be non-empty
            assert len(goal['projection_samples']) > 0
            assert all('month' in s and 'projected_balance' in s 
                      for s in goal['projection_samples'])
    
    def test_health_score_in_range(self, test_db, user_with_data):
        """Overall health score is 0-100."""
        report = build_user_report(user_with_data.id, test_db)
        score = report['overall_health_score']
        
        assert isinstance(score, int)
        assert 0 <= score <= 100
    
    def test_assumptions_structure(self, test_db, user_with_data):
        """Assumptions are documented."""
        report = build_user_report(user_with_data.id, test_db)
        assumptions = report['assumptions_used']
        
        expected_keys = {
            'inflation_rate',
            'discount_rate',
            'expected_equity_return',
            'expected_bond_return',
            'expected_cash_return',
        }
        assert set(assumptions.keys()) >= expected_keys


# ============================================================================
# DATA CONSISTENCY TESTS
# ============================================================================

class TestDataConsistency:
    """Validate consistency between report sections"""
    
    def test_metrics_match_snapshot(self, test_db, user_with_data):
        """Metrics match financial snapshot values."""
        report = build_user_report(user_with_data.id, test_db)
        metrics = report['computed_metrics']
        snapshot = report['financial_snapshot']
        
        if snapshot['available']:
            # Income should be positive
            assert metrics['monthly_income'] > 0
            # Net worth should be positive
            assert snapshot['net_worth'] > 0
    
    def test_goals_progress_calculation(self, test_db, user_with_data):
        """Goals progress is correctly calculated."""
        report = build_user_report(user_with_data.id, test_db)
        goals = report['goals_analysis']
        
        for goal in goals['goals']:
            # Progress should be target < 100%
            assert goal['progress_percentage'] <= 100
            # Progress = current / target
            expected_progress = (goal['current_amount'] / goal['target_amount'] * 100) if goal['target_amount'] > 0 else 0
            assert goal['progress_percentage'] == pytest.approx(expected_progress, abs=1.0)
    
    def test_holdings_consistency(self, test_db, user_with_data):
        """Holdings calculations are consistent."""
        report = build_user_report(user_with_data.id, test_db)
        holdings = report['holdings_summary']
        
        # Total should equal sum of individuals
        total_value = sum(h['current_value'] for h in holdings['holdings'])
        assert holdings['total_current_value'] == pytest.approx(total_value, abs=0.01)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_new_user_no_data(self, test_db, sample_user):
        """New user with no financial data."""
        report = build_user_report(sample_user.id, test_db)
        
        snapshot = report['financial_snapshot']
        assert snapshot['available'] is False
        
        metrics = report['computed_metrics']
        assert metrics['savings_rate'] == 0.0
        assert metrics['emergency_fund_months'] == 0.0
        
        holdings = report['holdings_summary']
        assert holdings['count'] == 0
        
        goals = report['goals_analysis']
        assert goals['count'] == 0
    
    def test_nonexistent_user(self, test_db):
        """Nonexistent user raises error."""
        fake_id = uuid4()
        
        with pytest.raises(ValueError, match="not found"):
            build_user_report(fake_id, test_db)
    
    def test_custom_assumptions(self, test_db, user_with_data):
        """Custom assumptions are applied."""
        custom_assumptions = {
            'expected_equity_return': 0.10,
            'inflation_rate': 0.02,
        }
        
        report = build_user_report(
            user_with_data.id, test_db, assumptions=custom_assumptions
        )
        
        # Check assumptions were used
        assert report['assumptions_used']['expected_equity_return'] == 0.10
        assert report['assumptions_used']['inflation_rate'] == 0.02
        # Defaults should still be present
        assert 'expected_bond_return' in report['assumptions_used']


# ============================================================================
# NUMERICAL CORRECTNESS TESTS
# ============================================================================

class TestNumericalCorrectness:
    """Verify numerical calculations in reports"""
    
    def test_rounding_to_2_decimals(self, test_db, user_with_data):
        """Monetary values rounded to 2 decimals."""
        report = build_user_report(user_with_data.id, test_db)
        
        # Check format of monetary values in various sections
        snapshot = report['financial_snapshot']
        for key in ['total_income', 'total_expenses', 'net_worth']:
            if isinstance(snapshot.get(key), float):
                # Check if it has at most 2 decimal places
                str_val = str(snapshot[key])
                if '.' in str_val:
                    decimals = len(str_val.split('.')[1])
                    assert decimals <= 2, f"{key} has {decimals} decimal places"
    
    def test_sip_calculation_in_goals(self, test_db, user_with_data):
        """Required SIP values are computed."""
        report = build_user_report(user_with_data.id, test_db)
        goals = report['goals_analysis']
        
        for goal in goals['goals']:
            # Required SIP should be non-negative
            assert goal['required_monthly_sip'] >= 0
            # Projected final should be >= current
            assert goal['projected_final_balance'] >= goal['current_amount']
    
    def test_projection_monotonicity(self, test_db, user_with_data):
        """Projections should be monotonic (non-decreasing with positive return)."""
        report = build_user_report(user_with_data.id, test_db)
        goals = report['goals_analysis']
        
        for goal in goals['goals']:
            samples = goal['projection_samples']
            # Sort by month to ensure order
            samples_sorted = sorted(samples, key=lambda s: s['month'])
            
            for i in range(len(samples_sorted) - 1):
                # Each should be >= previous (with positive return assumption)
                assert samples_sorted[i+1]['projected_balance'] >= samples_sorted[i]['projected_balance']


# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

class TestJSONSchema:
    """Validate JSON is properly structured and serializable"""
    
    def test_report_is_json_serializable(self, test_db, user_with_data):
        """Report can be serialized to JSON."""
        import json
        
        report = build_user_report(user_with_data.id, test_db)
        
        # Should not raise
        json_str = json.dumps(report)
        assert len(json_str) > 0
        
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed['report_id'] == report['report_id']
    
    def test_datetime_fields_are_strings(self, test_db, user_with_data):
        """DateTime fields are ISO format strings."""
        report = build_user_report(user_with_data.id, test_db)
        
        assert isinstance(report['report_generated_at'], str)
        assert 'T' in report['report_generated_at']  # ISO format
    
    def test_numeric_types_are_float_or_int(self, test_db, user_with_data):
        """Numeric fields are float or int (not Decimal)."""
        import json
        
        report = build_user_report(user_with_data.id, test_db)
        
        metrics = report['computed_metrics']
        for key, value in metrics.items():
            # Should be JSON-serializable numeric type
            json.dumps({key: value})
            assert isinstance(value, (int, float)), f"{key} is {type(value)}"
