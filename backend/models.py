"""
SQLAlchemy ORM models for database entities.

This module defines the database schema using SQLAlchemy declarative base.
Models are designed to be migrated with Alembic.

Common patterns:
- Use UUID primary keys for distributed systems
- Add created_at/updated_at timestamps
- Use descriptive column names with proper indexes
- Document relationships clearly

Example:
    class Portfolio(Base):
        __tablename__ = "portfolios"
        
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
        created_at = Column(DateTime, default=datetime.utcnow)
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, UUID
from sqlalchemy.orm import declarative_base

# Base class for all ORM models
Base = declarative_base()


class User(Base):
    """
    User account model.
    
    Attributes:
        id: Unique identifier
        email: User email address (unique)
        name: Full name
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(id={self.id}, email={self.email})>"


class Portfolio(Base):
    """
    Investment portfolio model.
    
    Attributes:
        id: Unique identifier
        user_id: Foreign key to user
        name: Portfolio name
        description: Portfolio description
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Portfolio(id={self.id}, user_id={self.user_id})>"


# TODO: Add models as project evolves
# - FinancialGoal
# - Transaction
# - Performance
# - Alert
