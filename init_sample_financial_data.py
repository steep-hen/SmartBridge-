#!/usr/bin/env python3
"""Initialize comprehensive sample financial data for Financial Dashboard."""

import sys
sys.path.insert(0, '.')

from uuid import UUID
from datetime import datetime, date, timedelta
from decimal import Decimal
from backend.db import SessionLocal
from backend.models import (
    User, FinancialSummary, Holding, Goal, Transaction, MarketPrice
)

# Sample user IDs matching init_demo_users.py
USERS = [
    "550e8400-e29b-41d4-a716-446655440001",  # Alex
    "550e8400-e29b-41d4-a716-446655440002",  # Priya
    "550e8400-e29b-41d4-a716-446655440003",  # James
]

EXPENSE_CATEGORIES = [
    "Housing", "Transportation", "Food & Dining", "Utilities",
    "Healthcare", "Entertainment", "Shopping", "Subscriptions"
]

def create_financial_summary(user_id: str, db):
    """Create financial summary for user."""
    # Check if already exists
    existing = db.query(FinancialSummary).filter(
        FinancialSummary.user_id == user_id
    ).first()
    
    if existing:
        print(f"✓ Financial summary exists for {user_id}")
        return existing
    
    summary = FinancialSummary(
        user_id=user_id,
        year=datetime.now().year,
        total_income=Decimal("720000.00"),  # $60,000/month × 12
        total_expenses=Decimal("540000.00"),  # $45,000/month × 12
        total_savings=Decimal("180000.00"),  # Difference
        net_worth=Decimal("8500000.00"),  # Includes home equity
        month=12,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(summary)
    db.commit()
    print(f"✓ Created financial summary for {user_id}")
    return summary

def create_holdings(user_id: str, db):
    """Create sample holdings for user."""
    holdings_data = [
        {
            "ticker": "VOO",
            "asset_type": "ETF",
            "quantity": Decimal("500"),
            "current_value": Decimal("2500000"),
            "average_cost": Decimal("2250000"),
        },
        {
            "ticker": "BND",
            "asset_type": "ETF",
            "quantity": Decimal("1000"),
            "current_value": Decimal("1200000"),
            "average_cost": Decimal("1100000"),
        },
        {
            "ticker": "VTI",
            "asset_type": "ETF",
            "quantity": Decimal("300"),
            "current_value": Decimal("1100000"),
            "average_cost": Decimal("1050000"),
        },
        {
            "ticker": "VGV",
            "asset_type": "ETF",
            "quantity": Decimal("200"),
            "current_value": Decimal("900000"),
            "average_cost": Decimal("840000"),
        },
        {
            "ticker": "MSFT",
            "asset_type": "STOCK",
            "quantity": Decimal("100"),
            "current_value": Decimal("350000"),
            "average_cost": Decimal("310000"),
        },
        {
            "ticker": "AAPL",
            "asset_type": "STOCK",
            "quantity": Decimal("150"),
            "current_value": Decimal("320000"),
            "average_cost": Decimal("280000"),
        },
        {
            "ticker": "GOOGL",
            "asset_type": "STOCK",
            "quantity": Decimal("50"),
            "current_value": Decimal("420000"),
            "average_cost": Decimal("385000"),
        },
        {
            "ticker": "QQQ",
            "asset_type": "ETF",
            "quantity": Decimal("200"),
            "current_value": Decimal("800000"),
            "average_cost": Decimal("720000"),
        },
        {
            "ticker": "SPY",
            "asset_type": "ETF",
            "quantity": Decimal("250"),
            "current_value": Decimal("1200000"),
            "average_cost": Decimal("1050000"),
        },
        {
            "ticker": "VDIGX",
            "asset_type": "MUTUAL_FUND",
            "quantity": Decimal("150"),
            "current_value": Decimal("750000"),
            "average_cost": Decimal("700000"),
        },
        {
            "ticker": "BTC",
            "asset_type": "CRYPTO",
            "quantity": Decimal("0.5"),
            "current_value": Decimal("180000"),
            "average_cost": Decimal("160000"),
        },
        {
            "ticker": "ETH",
            "asset_type": "CRYPTO",
            "quantity": Decimal("5"),
            "current_value": Decimal("95000"),
            "average_cost": Decimal("85000"),
        }
    ]
    
    created = 0
    for holding_data in holdings_data:
        existing = db.query(Holding).filter(
            (Holding.user_id == user_id) &
            (Holding.ticker == holding_data["ticker"])
        ).first()
        
        if existing:
            print(f"  ✓ Holding {holding_data['ticker']} exists")
            continue
        
        holding = Holding(
            user_id=user_id,
            ticker=holding_data["ticker"],
            asset_type=holding_data["asset_type"],
            quantity=holding_data["quantity"],
            current_value=holding_data["current_value"],
            average_cost=holding_data["average_cost"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(holding)
        created += 1
    
    if created > 0:
        db.commit()
        print(f"✓ Created {created} holdings for {user_id}")

def create_goals(user_id: str, db):
    """Create sample financial goals for user."""
    goals_data = [
        {
            "goal_name": "Emergency Fund",
            "goal_type": "SAVINGS",
            "target_amount": Decimal("500000"),
            "current_amount": Decimal("450000"),
            "target_date": date.today() + timedelta(days=180),
            "status": "ON_TRACK",
            "priority": "HIGH",
        },
        {
            "goal_name": "Home Purchase",
            "goal_type": "INVESTMENT",
            "target_amount": Decimal("5000000"),
            "current_amount": Decimal("2850000"),
            "target_date": date.today() + timedelta(days=1740),  # 58 months
            "status": "IN_PROGRESS",
            "priority": "HIGH",
        },
        {
            "goal_name": "Child Education",
            "goal_type": "INVESTMENT",
            "target_amount": Decimal("2000000"),
            "current_amount": Decimal("800000"),
            "target_date": date.today() + timedelta(days=2460),  # 82 months
            "status": "IN_PROGRESS",
            "priority": "HIGH",
        },
        {
            "goal_name": "Retirement Fund",
            "goal_type": "INVESTMENT",
            "target_amount": Decimal("10000000"),
            "current_amount": Decimal("3500000"),
            "target_date": date.today() + timedelta(days=9060),  # 302 months
            "status": "IN_PROGRESS",
            "priority": "MEDIUM",
        },
        {
            "goal_name": "Vacation Fund",
            "goal_type": "SAVINGS",
            "target_amount": Decimal("500000"),
            "current_amount": Decimal("350000"),
            "target_date": date.today() + timedelta(days=270),
            "status": "ON_TRACK",
            "priority": "MEDIUM",
        },
    ]
    
    created = 0
    for goal_data in goals_data:
        existing = db.query(Goal).filter(
            (Goal.user_id == user_id) &
            (Goal.goal_name == goal_data["goal_name"])
        ).first()
        
        if existing:
            print(f"  ✓ Goal '{goal_data['goal_name']}' exists")
            continue
        
        goal = Goal(
            user_id=user_id,
            goal_name=goal_data["goal_name"],
            goal_type=goal_data["goal_type"],
            target_amount=goal_data["target_amount"],
            current_amount=goal_data["current_amount"],
            target_date=goal_data["target_date"],
            status=goal_data["status"],
            priority=goal_data["priority"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(goal)
        created += 1
    
    if created > 0:
        db.commit()
        print(f"✓ Created {created} goals for {user_id}")

def create_transactions(user_id: str, db):
    """Create sample transactions for user."""
    transactions_data = []
    
    # Create monthly transactions for the last 6 months with varied spending
    today = date.today()
    for month_offset in range(1, 7):  # Last 6 months instead of 3
        month_date = today - timedelta(days=30*month_offset)
        
        # Housing - largest expense
        transactions_data.append({
            "date": month_date,
            "description": "House Mortgage",
            "amount": Decimal("35000"),
            "category": "Housing",
            "transaction_type": "EXPENSE",
        })
        
        # Property Tax
        if month_offset % 3 == 0:  # Quarterly
            transactions_data.append({
                "date": month_date,
                "description": "Property Tax",
                "amount": Decimal("8500"),
                "category": "Housing",
                "transaction_type": "EXPENSE",
            })
        
        # Groceries - recurring
        transactions_data.append({
            "date": month_date + timedelta(days=2),
            "description": "Supermarket Grocery",
            "amount": Decimal("3500"),
            "category": "Food & Dining",
            "transaction_type": "EXPENSE",
        })
        
        # Restaurant
        transactions_data.append({
            "date": month_date + timedelta(days=7),
            "description": "Restaurant Dining",
            "amount": Decimal("2200"),
            "category": "Food & Dining",
            "transaction_type": "EXPENSE",
        })
        
        # Utilities
        transactions_data.append({
            "date": month_date + timedelta(days=5),
            "description": "Electric Company",
            "amount": Decimal("1500"),
            "category": "Utilities",
            "transaction_type": "EXPENSE",
        })
        
        # Internet/Phone
        transactions_data.append({
            "date": month_date + timedelta(days=10),
            "description": "Internet Service Provider",
            "amount": Decimal("800"),
            "category": "Utilities",
            "transaction_type": "EXPENSE",
        })
        
        # Transportation
        transactions_data.append({
            "date": month_date + timedelta(days=3),
            "description": "Gas Station",
            "amount": Decimal("2500"),
            "category": "Transportation",
            "transaction_type": "EXPENSE",
        })
        
        # Car Insurance
        if month_offset % 3 == 0:  # Quarterly
            transactions_data.append({
                "date": month_date,
                "description": "Car Insurance Premium",
                "amount": Decimal("3000"),
                "category": "Transportation",
                "transaction_type": "EXPENSE",
            })
        
        # Entertainment
        transactions_data.append({
            "date": month_date + timedelta(days=12),
            "description": "Movie Theater",
            "amount": Decimal("800"),
            "category": "Entertainment",
            "transaction_type": "EXPENSE",
        })
        
        # Gym Membership (Recurring Subscription)
        transactions_data.append({
            "date": month_date + timedelta(days=1),
            "description": "Gym Membership",
            "amount": Decimal("1200"),
            "category": "Subscriptions",
            "transaction_type": "EXPENSE",
        })
        
        # Streaming Services
        transactions_data.append({
            "date": month_date + timedelta(days=1),
            "description": "Netflix Subscription",
            "amount": Decimal("450"),
            "category": "Subscriptions",
            "transaction_type": "EXPENSE",
        })
        
        # Healthcare
        if month_offset % 2 == 0:
            transactions_data.append({
                "date": month_date + timedelta(days=15),
                "description": "Doctor Visit",
                "amount": Decimal("800"),
                "category": "Healthcare",
                "transaction_type": "EXPENSE",
            })
        
        # Shopping
        transactions_data.append({
            "date": month_date + timedelta(days=20),
            "description": "Clothing Store",
            "amount": Decimal("3000"),
            "category": "Shopping",
            "transaction_type": "EXPENSE",
        })
        
        # Income
        transactions_data.append({
            "date": month_date + timedelta(days=1),
            "description": "Monthly Salary",
            "amount": Decimal("72000"),
            "category": "Income",
            "transaction_type": "INCOME",
        })
    
    created = 0
    for trans_data in transactions_data:
        # Check if similar transaction exists (avoid duplicates)
        existing = db.query(Transaction).filter(
            (Transaction.user_id == user_id) &
            (Transaction.transaction_date == trans_data["date"]) &
            (Transaction.description == trans_data["description"])
        ).first()
        
        if existing:
            continue
        
        transaction = Transaction(
            user_id=user_id,
            transaction_date=trans_data["date"],
            description=trans_data["description"],
            amount=trans_data["amount"],
            category=trans_data["category"],
            transaction_type=trans_data["transaction_type"],
            created_at=datetime.utcnow(),
        )
        db.add(transaction)
        created += 1
    
    if created > 0:
        db.commit()
        print(f"✓ Created {created} transactions for {user_id}")

def init_financial_data():
    """Initialize all financial data for sample users."""
    db = SessionLocal()
    
    try:
        print("\n📊 Initializing Financial Dashboard sample data...")
        print("=" * 60)
        
        for user_id in USERS:
            print(f"\n👤 Processing user: {user_id}")
            
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"  ⚠️  User not found. Run init_demo_users.py first")
                continue
            
            print(f"  User: {user.name}")
            
            # Create financial data
            create_financial_summary(user_id, db)
            create_holdings(user_id, db)
            create_goals(user_id, db)
            create_transactions(user_id, db)
        
        print("\n" + "=" * 60)
        print("✅ Successfully initialized Financial Dashboard sample data!")
        print("\nYou can now:")
        print("  - Run: streamlit run frontend/streamlit_app.py")
        print("  - Open: http://localhost:8501")
        print("  - Select a user from the dropdown to view their financial dashboard")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error initializing data: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        db.close()

if __name__ == "__main__":
    init_financial_data()
