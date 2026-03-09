"""Comprehensive API endpoint tests.

Tests for user management, financial reports, and AI advice endpoints.
Uses TestClient with in-memory SQLite database for isolation.

Test Coverage:
    - User CRUD operations
    - User profile retrieval with nested data
    - Financial report generation
    - Transaction filtering
    - API key authentication
    - Error handling and validation
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import Base, User, FinancialSummary, Transaction, Goal, Holding
from backend.db import get_db
from backend.config import settings


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
def client(test_db: Session):
    """Create FastAPI test client with test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        phone="+1-555-1234",
        gender="M",
        country="United States",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user_with_data(test_db: Session, test_user: User) -> User:
    """Create a test user with financial data."""
    # Add financial summary
    summary = FinancialSummary(
        user_id=test_user.id,
        year=2024,
        month=1,
        total_income=Decimal("5000.00"),
        total_expenses=Decimal("3000.00"),
        total_savings=Decimal("1500.00"),
        total_investments=Decimal("500.00"),
        net_worth=Decimal("50000.00"),
    )
    test_db.add(summary)
    
    # Add transactions
    for i in range(5):
        txn = Transaction(
            user_id=test_user.id,
            transaction_date=date(2024, 1, 15),
            amount=Decimal("100.00"),
            category="Groceries",
            merchant_name=f"Store {i}",
            transaction_type="EXPENSE",
            payment_method="CARD",
        )
        test_db.add(txn)
    
    # Add goal
    goal = Goal(
        user_id=test_user.id,
        goal_name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("5000.00"),
        goal_type="SAVINGS",
        status="ACTIVE",
        priority="HIGH",
    )
    test_db.add(goal)
    
    # Add holding
    holding = Holding(
        user_id=test_user.id,
        ticker="AAPL",
        quantity=Decimal("10.00"),
        average_cost=Decimal("150.00"),
        current_value=Decimal("1850.00"),
        asset_type="EQUITY",
        purchase_date=date(2023, 6, 15),
    )
    test_db.add(holding)
    
    test_db.commit()
    test_db.refresh(test_user)
    return test_user


# ============================================================================
# USER ENDPOINT TESTS
# ============================================================================

class TestUserEndpoints:
    """Test user CRUD endpoints."""
    
    def test_create_user_success(self, client):
        """Test successful user creation."""
        response = client.post(
            "/users",
            json={
                "email": "newuser@example.com",
                "name": "New User",
                "phone": "+1-555-9999",
                "gender": "F",
                "country": "Canada",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_user_duplicate_email(self, client, test_user):
        """Test that duplicate emails are rejected."""
        response = client.post(
            "/users",
            json={
                "email": test_user.email,
                "name": "Another User",
            },
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_user_missing_required_field(self, client):
        """Test validation of required fields."""
        response = client.post(
            "/users",
            json={
                "email": "test@example.com",
                # Missing name
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_user_invalid_email(self, client):
        """Test email format validation."""
        response = client.post(
            "/users",
            json={
                "email": "not-an-email",
                "name": "Test User",
            },
        )
        
        assert response.status_code == 422
    
    def test_list_users(self, client, test_db: Session):
        """Test user list endpoint."""
        # Create multiple users
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
            )
            test_db.add(user)
        test_db.commit()
        
        response = client.get("/users?skip=0&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
    
    def test_list_users_pagination(self, client, test_db: Session):
        """Test user list pagination."""
        # Create 15 users
        for i in range(15):
            user = User(
                email=f"user{i}@example.com",
                name=f"User {i}",
            )
            test_db.add(user)
        test_db.commit()
        
        # Get first page
        response1 = client.get("/users?skip=0&limit=10")
        assert response1.status_code == 200
        assert len(response1.json()) == 10
        
        # Get second page
        response2 = client.get("/users?skip=10&limit=10")
        assert response2.status_code == 200
        assert len(response2.json()) == 5
    
    def test_get_user_profile(self, client, test_user_with_data):
        """Test getting user profile with financial data."""
        response = client.get(f"/users/{test_user_with_data.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user_with_data.id)
        assert data["email"] == test_user_with_data.email
        assert "financial_summaries" in data
        assert "holdings" in data
        assert "goals" in data
    
    def test_get_nonexistent_user(self, client):
        """Test 404 when user doesn't exist."""
        fake_id = uuid4()
        response = client.get(f"/users/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_user_transactions(self, client, test_user_with_data):
        """Test getting user transactions."""
        response = client.get(
            f"/users/{test_user_with_data.id}/transactions"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert len(data["items"]) == 5
        assert data["total"] == 5
    
    def test_get_user_transactions_pagination(self, client, test_user_with_data, test_db: Session):
        """Test transaction pagination."""
        # Add more transactions
        for i in range(25):
            txn = Transaction(
                user_id=test_user_with_data.id,
                transaction_date=date(2024, 1, 15 + (i % 15)),
                amount=Decimal("50.00"),
                category="Test",
                transaction_type="EXPENSE",
            )
            test_db.add(txn)
        test_db.commit()
        
        response = client.get(
            f"/users/{test_user_with_data.id}/transactions?skip=0&limit=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 30  # 5 from fixture + 25 added
    
    def test_get_user_transactions_filter_by_month(self, client, test_user_with_data):
        """Test filtering transactions by month."""
        response = client.get(
            f"/users/{test_user_with_data.id}/transactions?month=2024-01"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5  # All from January 2024
    
    def test_get_user_transactions_filter_by_category(self, client, test_user_with_data, test_db: Session):
        """Test filtering transactions by category."""
        # Add transaction with different category
        txn = Transaction(
            user_id=test_user_with_data.id,
            transaction_date=date(2024, 1, 15),
            amount=Decimal("50.00"),
            category="Salary",
            transaction_type="INCOME",
        )
        test_db.add(txn)
        test_db.commit()
        
        response = client.get(
            f"/users/{test_user_with_data.id}/transactions?category=Groceries"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
    
    def test_get_user_transactions_invalid_month_format(self, client, test_user):
        """Test error handling for invalid month format."""
        response = client.get(
            f"/users/{test_user.id}/transactions?month=invalid"
        )
        
        assert response.status_code == 400
        assert "Invalid month format" in response.json()["detail"]


# ============================================================================
# REPORT ENDPOINT TESTS
# ============================================================================

class TestReportEndpoints:
    """Test financial report endpoints."""
    
    def test_generate_report_success(self, client, test_user_with_data):
        """Test successful report generation."""
        response = client.get(f"/reports/{test_user_with_data.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user_with_data.id)
        assert data["total_income"] == 5000.0
        assert data["total_expenses"] == 3000.0
        assert data["savings_amount"] == 1500.0
        assert "savings_rate" in data
        assert "net_worth" in data
        assert "goals_summary" in data
        assert "portfolio_summary" in data
    
    def test_generate_report_user_not_found(self, client):
        """Test 404 when generating report for nonexistent user."""
        fake_id = uuid4()
        response = client.get(f"/reports/{fake_id}")
        
        assert response.status_code == 404
    
    def test_generate_report_no_financial_data(self, client, test_user):
        """Test report generation when no financial data exists."""
        response = client.get(f"/reports/{test_user.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_income"] == 0.0
        assert data["total_expenses"] == 0.0
        assert data["savings_rate"] == 0.0


# ============================================================================
# AI ADVICE ENDPOINT TESTS
# ============================================================================

class TestAIAdviceEndpoints:
    """Test AI advice endpoints."""
    
    def test_generate_advice_without_api_key(self, client, test_user):
        """Test that API key is required."""
        response = client.post(
            f"/ai/advice/{test_user.id}",
            json={"question": "How can I save more?"},
        )
        
        assert response.status_code == 401
    
    def test_generate_advice_invalid_api_key(self, client, test_user):
        """Test rejection of invalid API key."""
        response = client.post(
            f"/ai/advice/{test_user.id}",
            json={"question": "How can I save more?"},
            headers={"X-API-KEY": "invalid-key"},
        )
        
        assert response.status_code == 401
    
    def test_generate_advice_success(self, client, test_user_with_data):
        """Test successful advice generation with valid API key."""
        response = client.post(
            f"/ai/advice/{test_user_with_data.id}",
            json={"question": "How can I improve my savings rate?"},
            headers={"X-API-KEY": settings.secret_key},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(test_user_with_data.id)
        assert "advice" in data
        assert len(data["advice"]) > 0
        assert "source" in data  # local or gemini
        assert "confidence" in data
        assert "generated_at" in data
    
    def test_generate_advice_user_not_found(self, client):
        """Test 404 when user doesn't exist."""
        fake_id = uuid4()
        response = client.post(
            f"/ai/advice/{fake_id}",
            json={"question": "How can I save more?"},
            headers={"X-API-KEY": settings.secret_key},
        )
        
        assert response.status_code == 404


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAPIIntegration:
    """Integration tests for complete workflows."""
    
    def test_create_user_with_data_workflow(self, client, test_db, test_user_with_data):
        """Test workflow: create user -> add data -> get report."""
        # User already created with data via fixture
        
        # Get user profile
        profile_response = client.get(f"/users/{test_user_with_data.id}")
        assert profile_response.status_code == 200
        
        # Get financial report
        report_response = client.get(f"/reports/{test_user_with_data.id}")
        assert report_response.status_code == 200
        
        # Get transactions
        txn_response = client.get(
            f"/users/{test_user_with_data.id}/transactions"
        )
        assert txn_response.status_code == 200
    
    def test_full_api_workflow(self, client, test_db):
        """Test complete user journey through API."""
        # 1. Create user
        create_response = client.post(
            "/users",
            json={
                "email": "workflow@example.com",
                "name": "Workflow Test",
            },
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        
        # 2. Get user profile (should have empty financial data)
        profile_response = client.get(f"/users/{user_id}")
        assert profile_response.status_code == 200
        
        # 3. Get empty report
        report_response = client.get(f"/reports/{user_id}")
        assert report_response.status_code == 200
        report_data = report_response.json()
        assert report_data["total_income"] == 0.0
        
        # 4. Get empty transactions
        txn_response = client.get(f"/users/{user_id}/transactions")
        assert txn_response.status_code == 200
        assert txn_response.json()["total"] == 0
        
        # 5. Get AI advice (protected)
        advice_response = client.post(
            f"/ai/advice/{user_id}",
            json={"question": "What's my financial status?"},
            headers={"X-API-KEY": settings.secret_key},
        )
        assert advice_response.status_code == 200


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_uuid_format(self, client):
        """Test handling of invalid UUID formats."""
        response = client.get("/users/not-a-uuid")
        assert response.status_code == 422  # Validation error
    
    def test_pagination_limits(self, client, test_db):
        """Test pagination limit constraints."""
        # Test skip < 0
        response = client.get("/users?skip=-1")
        assert response.status_code == 422
        
        # Test limit > 100
        response = client.get("/users?limit=101")
        assert response.status_code == 422
        
        # Test valid limits
        response = client.get("/users?skip=0&limit=100")
        assert response.status_code == 200
