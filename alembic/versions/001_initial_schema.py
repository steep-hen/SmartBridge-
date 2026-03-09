"""Initial schema creation

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema tables."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('date_of_birth', sa.Date()),
        sa.Column('gender', sa.String(1)),
        sa.Column('country', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Create financial_summary table
    op.create_table(
        'financial_summary',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('total_income', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_expenses', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_savings', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_investments', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('net_worth', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', 'month', name='uq_user_year_month'),
        sa.CheckConstraint('month >= 1 AND month <= 12', name='ck_valid_month'),
        sa.CheckConstraint('total_income >= 0', name='ck_income_nonneg'),
        sa.CheckConstraint('total_expenses >= 0', name='ck_expenses_nonneg')
    )
    op.create_index('ix_financial_summary_user_id', 'financial_summary', ['user_id'])
    op.create_index('idx_user_year_month', 'financial_summary', ['user_id', 'year', 'month'])
    
    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('merchant_name', sa.String(255)),
        sa.Column('transaction_type', sa.String(20)),
        sa.Column('payment_method', sa.String(20)),
        sa.Column('description', sa.Text()),
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('amount > 0', name='ck_amount_positive')
    )
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_transaction_date', 'transactions', ['transaction_date'])
    op.create_index('ix_transactions_category', 'transactions', ['category'])
    op.create_index('idx_user_date', 'transactions', ['user_id', 'transaction_date'])
    op.create_index('idx_user_category', 'transactions', ['user_id', 'category'])
    
    # Create goals table
    op.create_table(
        'goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('goal_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('target_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('target_date', sa.Date()),
        sa.Column('goal_type', sa.String(50)),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('priority', sa.String(10)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('target_amount > 0', name='ck_target_amount_positive'),
        sa.CheckConstraint('current_amount >= 0', name='ck_current_amount_nonneg')
    )
    op.create_index('ix_goals_user_id', 'goals', ['user_id'])
    
    # Create holdings table
    op.create_table(
        'holdings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('average_cost', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_value', sa.Numeric(precision=15, scale=2)),
        sa.Column('asset_type', sa.String(50)),
        sa.Column('purchase_date', sa.Date()),
        sa.Column('last_updated', sa.Date()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity > 0', name='ck_quantity_positive'),
        sa.CheckConstraint('average_cost > 0', name='ck_cost_positive')
    )
    op.create_index('ix_holdings_user_id', 'holdings', ['user_id'])
    op.create_index('ix_holdings_ticker', 'holdings', ['ticker'])
    op.create_index('idx_user_ticker', 'holdings', ['user_id', 'ticker'])
    
    # Create market_prices table
    op.create_table(
        'market_prices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('price_date', sa.Date(), nullable=False),
        sa.Column('open_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('close_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('high_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('low_price', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('volume', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker', 'price_date', name='uq_ticker_date'),
        sa.CheckConstraint('open_price > 0', name='ck_open_positive'),
        sa.CheckConstraint('close_price > 0', name='ck_close_positive'),
        sa.CheckConstraint('high_price >= low_price', name='ck_high_gte_low')
    )
    op.create_index('ix_market_prices_ticker', 'market_prices', ['ticker'])
    op.create_index('ix_market_prices_price_date', 'market_prices', ['price_date'])
    op.create_index('idx_ticker_date', 'market_prices', ['ticker', 'price_date'])
    
    # Create consent_log table
    op.create_table(
        'consent_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consent_type', sa.String(100), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_consent_log_user_id', 'consent_log', ['user_id'])
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100)),
        sa.Column('details', postgresql.JSON()),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(45)),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    op.create_index('ix_audit_log_timestamp', 'audit_log', ['timestamp'])


def downgrade() -> None:
    """Drop all schema tables."""
    op.drop_table('audit_log')
    op.drop_table('consent_log')
    op.drop_table('market_prices')
    op.drop_table('holdings')
    op.drop_table('goals')
    op.drop_table('transactions')
    op.drop_table('financial_summary')
    op.drop_table('users')
