"""
SQLAlchemy ORM Models

Maps to PostgreSQL database schema defined in infra/sql/schema.sql.
Uses declarative base for model definition with UUID primary keys.
All models include proper relationships, indexes, and constraints.

Common patterns:
- UUID primary keys via postgresql UUID type
- created_at/updated_at timestamps on all entities
- Proper foreign keys with cascade delete where appropriate
- Indexes on frequently queried columns
- Document relationships and constraints
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import (
    Column, String, Integer, Numeric, Date, DateTime, Boolean, Text,
    ForeignKey, CheckConstraint, UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class User(Base):
    """User/Customer master table.
    
    Core user entity containing personal information and demographics.
    All financial data is linked to users via user_id foreign key.
    """
    __tablename__ = "users"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(String(1))  # M, F, O
    country = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - cascade delete on user deletion
    financial_summaries = relationship(
        "FinancialSummary",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    goals = relationship(
        "Goal",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    holdings = relationship(
        "Holding",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    consent_logs = relationship(
        "ConsentLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"


class FinancialSummary(Base):
    """Monthly financial snapshots per user.
    
    Aggregated finance metrics calculated monthly for each user.
    Used for financial analysis and reporting.
    Unique constraint on (user_id, year, month).
    """
    __tablename__ = "financial_summary"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    total_income = Column(Numeric(15, 2), nullable=False, default=0)
    total_expenses = Column(Numeric(15, 2), nullable=False, default=0)
    total_savings = Column(Numeric(15, 2), nullable=False, default=0)
    total_investments = Column(Numeric(15, 2), nullable=False, default=0)
    net_worth = Column(Numeric(15, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'year', 'month', name='uq_user_year_month'),
        CheckConstraint('month >= 1 AND month <= 12', name='ck_valid_month'),
        CheckConstraint('total_income >= 0', name='ck_income_nonneg'),
        CheckConstraint('total_expenses >= 0', name='ck_expenses_nonneg'),
        Index('idx_user_year_month', 'user_id', 'year', 'month'),
    )

    # Relationships
    user = relationship("User", back_populates="financial_summaries")

    def __repr__(self):
        return f"<FinancialSummary(user_id={self.user_id}, {self.year}-{self.month:02d}, net_worth={self.net_worth})>"


class Transaction(Base):
    """Financial transactions.
    
    Individual financial transactions (income, expense, investment).
    Records payment method, merchant, and recurring pattern.
    Indexed on user_id, date, and category for efficient queries.
    """
    __tablename__ = "transactions"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    transaction_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    merchant_name = Column(String(255))
    transaction_type = Column(String(20))  # INCOME, EXPENSE, INVESTMENT
    payment_method = Column(String(20))  # CARD, BANK_TRANSFER, CASH, CHECK
    description = Column(Text)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_amount_positive'),
        Index('idx_user_date', 'user_id', 'transaction_date'),
        Index('idx_user_category', 'user_id', 'category'),
    )

    # Relationships
    user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.id}, user={self.user_id}, amount={self.amount}, category={self.category})>"


class Goal(Base):
    """Financial goals and milestones.
    
    User-defined financial goals with target amounts and dates.
    Tracks progress via current_amount and status.
    Supports different goal types: SAVINGS, INVESTMENT, DEBT_PAYOFF, etc.
    """
    __tablename__ = "goals"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    goal_name = Column(String(255), nullable=False)
    description = Column(Text)
    target_amount = Column(Numeric(15, 2), nullable=False)
    current_amount = Column(Numeric(15, 2), default=0)
    target_date = Column(Date)
    goal_type = Column(String(50))  # SAVINGS, INVESTMENT, DEBT_PAYOFF, EDUCATION, RETIREMENT
    status = Column(String(20), default="ACTIVE")  # ACTIVE, COMPLETED, ABANDONED
    priority = Column(String(10))  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint('target_amount > 0', name='ck_target_amount_positive'),
        CheckConstraint('current_amount >= 0', name='ck_current_amount_nonneg'),
    )

    # Relationships
    user = relationship("User", back_populates="goals")

    def __repr__(self):
        return f"<Goal(id={self.id}, user={self.user_id}, name={self.goal_name}, progress={self.current_amount}/{self.target_amount})>"


class Holding(Base):
    """Investment portfolio positions.
    
    Records individual investment holdings (stocks, ETFs, crypto, bonds).
    Tracks quantity, cost basis, and current market value.
    last_updated used for price reconciliation.
    """
    __tablename__ = "holdings"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    ticker = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(18, 8), nullable=False)
    average_cost = Column(Numeric(15, 2), nullable=False)
    current_value = Column(Numeric(15, 2))
    asset_type = Column(String(50))  # EQUITY, ETF, MUTUAL_FUND, CRYPTO, BOND
    purchase_date = Column(Date)
    last_updated = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_quantity_positive'),
        CheckConstraint('average_cost > 0', name='ck_cost_positive'),
        Index('idx_user_ticker', 'user_id', 'ticker'),
    )

    # Relationships
    user = relationship("User", back_populates="holdings")

    def __repr__(self):
        return f"<Holding(id={self.id}, user={self.user_id}, ticker={self.ticker}, qty={self.quantity})>"


class MarketPrice(Base):
    """Historical market price data (OHLCV).
    
    Time series market data for securities.
    Used for portfolio valuation and historical analysis.
    Unique constraint on (ticker, price_date).
    """
    __tablename__ = "market_prices"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker = Column(String(20), nullable=False, index=True)
    price_date = Column(Date, nullable=False, index=True)
    open_price = Column(Numeric(15, 2), nullable=False)
    close_price = Column(Numeric(15, 2), nullable=False)
    high_price = Column(Numeric(15, 2), nullable=False)
    low_price = Column(Numeric(15, 2), nullable=False)
    volume = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('ticker', 'price_date', name='uq_ticker_date'),
        CheckConstraint('open_price > 0', name='ck_open_positive'),
        CheckConstraint('close_price > 0', name='ck_close_positive'),
        CheckConstraint('high_price >= low_price', name='ck_high_gte_low'),
        Index('idx_ticker_date', 'ticker', 'price_date'),
    )

    def __repr__(self):
        return f"<MarketPrice(ticker={self.ticker}, date={self.price_date}, close={self.close_price})>"


class ConsentLog(Base):
    """User consent/privacy tracking.
    
    Audit trail for user consents (GDPR, CCPA compliance).
    Records consent type, decision, and timestamp.
    """
    __tablename__ = "consent_log"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    consent_type = Column(String(100), nullable=False)
    granted = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text)

    # Relationships
    user = relationship("User", back_populates="consent_logs")

    def __repr__(self):
        return f"<ConsentLog(user={self.user_id}, type={self.consent_type}, granted={self.granted})>"


class AuditLog(Base):
    """System audit trail.
    
    Records all significant actions for compliance and debugging.
    Tracks who did what, when, and from where (IP address).
    JSON details field allows flexible action-specific data.
    """
    __tablename__ = "audit_log"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(45))

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(user={self.user_id}, action={self.action}, timestamp={self.timestamp})>"
