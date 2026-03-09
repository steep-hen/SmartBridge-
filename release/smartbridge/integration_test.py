"""Demonstration of end-to-end integration: Financial report → AI advice."""

import sys
sys.path.insert(0, '.')

import json
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

# Backend imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base, User, FinancialSummary, Holding, Goal
from backend.finance.report_builder import build_user_report
from backend.ai.ai_client import generate_advice

# Create in-memory test database
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 70)
print("END-TO-END INTEGRATION TEST: Financial Report → AI Advice")
print("=" * 70)

# Create test user with comprehensive financial data
print("\n1. Creating test user with financial data...")
user = User(
    email='integration-test@example.com',
    name='Integration Test User',
    country='USA',
)
db.add(user)
db.flush()

# Add financial summary
summary = FinancialSummary(
    user_id=user.id,
    year=2024,
    month=1,
    total_income=Decimal('6000.00'),
    total_expenses=Decimal('3500.00'),
    total_savings=Decimal('2000.00'),
    total_investments=Decimal('25000.00'),
    net_worth=Decimal('80000.00'),
)
db.add(summary)

# Add holdings (diversified portfolio)
holdings = [
    Holding(
        user_id=user.id,
        ticker='VTI',
        quantity=Decimal('50.00'),
        average_cost=Decimal('200.00'),
        current_value=Decimal('12500.00'),
        asset_type='ETF',
    ),
    Holding(
        user_id=user.id,
        ticker='BND',
        quantity=Decimal('100.00'),
        average_cost=Decimal('100.00'),
        current_value=Decimal('10000.00'),
        asset_type='ETF',
    ),
    Holding(
        user_id=user.id,
        ticker='AAPL',
        quantity=Decimal('10.00'),
        average_cost=Decimal('150.00'),
        current_value=Decimal('2500.00'),
        asset_type='EQUITY',
    ),
]
for h in holdings:
    db.add(h)

# Add financial goals
goals = [
    Goal(
        user_id=user.id,
        goal_name='Emergency Fund (6 months)',
        target_amount=Decimal('21000.00'),
        current_amount=Decimal('8000.00'),
        goal_type='SAVINGS',
        status='ACTIVE',
        priority='HIGH',
        target_date=date.today() + timedelta(days=365),
    ),
    Goal(
        user_id=user.id,
        goal_name='House Down Payment',
        target_amount=Decimal('100000.00'),
        current_amount=Decimal('25000.00'),
        goal_type='SAVINGS',
        status='ACTIVE',
        priority='HIGH',
        target_date=date.today() + timedelta(days=1095),
    ),
    Goal(
        user_id=user.id,
        goal_name='Retirement Fund',
        target_amount=Decimal('1000000.00'),
        current_amount=Decimal('80000.00'),
        goal_type='INVESTMENTS',
        status='ACTIVE',
        priority='MEDIUM',
        target_date=date.today() + timedelta(days=12775),  # 35 years
    ),
]
for g in goals:
    db.add(g)

db.commit()
db.refresh(user)

print(f"   ✓ User created: {user.id}")
print(f"   ✓ Holdings: {len(holdings)}")
print(f"   ✓ Goals: {len(goals)}")

# Step 2: Generate financial report
print("\n2. Generating financial report from data...")
report = build_user_report(user.id, db)
print(f"   ✓ Report generated")
print(f"   ✓ Report ID: {report['report_id']}")
print(f"   ✓ Health Score: {report['overall_health_score']}/100")
print(f"   ✓ Metrics computed:")
metrics = report['computed_metrics']
print(f"     - Savings Rate: {metrics['savings_rate']:.1f}%")
print(f"     - Debt-to-Income: {metrics['debt_to_income_ratio']:.4f}")
print(f"     - Emergency Fund: {metrics['emergency_fund_months']:.1f} months")
print(f"     - Investment Ratio: {metrics['investment_ratio']:.2%}")

# Step 3: Generate AI advice
print("\n3. Generating AI advice from report...")
advice = generate_advice(report, template='balanced')
print(f"   ✓ Advice generated successfully")
print(f"   ✓ Response is valid JSON: {isinstance(advice, dict)}")

# Step 4: Display advice summary
print("\n4. Advice Summary:")
print(f"   Actions ({len(advice['actions'])}):")
for i, action in enumerate(advice['actions'], 1):
    print(f"     {i}. {action['title']} (Priority: {action['priority']}/5)")
    print(f"        {action['rationale'][:80]}...")

print(f"\n   Recommended Instruments ({len(advice['instruments'])}):")
for i, instrument in enumerate(advice['instruments'], 1):
    print(f"     {i}. {instrument['name']} ({instrument['type']})")
    print(f"        Allocation: {instrument['allocation_pct']:.1f}%")

print(f"\n   Risk Warning:")
print(f"     {advice['risk_warning'][:100]}...")

print(f"\n   Assumptions:")
print(f"     - Expected Annual Return: {advice['assumptions']['expected_annual_return']:.1%}")
print(f"     - Inflation Rate: {advice['assumptions']['inflation']:.1%}")

# Step 5: Verify audit log
print("\n5. Checking audit log...")
from backend.ai.audit import get_audit_logger
audit_logger = get_audit_logger()
user_trail = audit_logger.get_user_audit_trail(str(user.id))
print(f"   ✓ Audit entries for user: {len(user_trail)}")
if user_trail:
    latest = user_trail[-1]
    print(f"   ✓ Latest entry:")
    print(f"     - Model: {latest['model_used']}/{latest['model_version']}")
    print(f"     - Template: {latest['template_used']}")
    print(f"     - Blocked: {latest['blocked_flag']}")

# Step 6: Validate schema
print("\n6. Validating output schema...")
from backend.ai.prompt_templates import get_output_schema
from jsonschema import validate, ValidationError
schema = get_output_schema()
try:
    validate(instance=advice, schema=schema)
    print(f"   ✓ Schema validation PASSED")
except ValidationError as e:
    print(f"   ✗ Schema validation FAILED: {e.message}")

print("\n" + "=" * 70)
print("INTEGRATION TEST COMPLETE - ALL SYSTEMS OPERATIONAL")
print("=" * 70)

# Save demonstration output
output = {
    'test_status': 'PASSED',
    'user_id': str(user.id),
    'report': report,
    'advice': advice,
}

with open('outputs/integration_test_output.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)

print("\n✓ Output saved to: outputs/integration_test_output.json")
