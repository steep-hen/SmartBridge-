"""
Database connection factory and session management.

Provides SQLAlchemy engine and session factory for ORM operations.
Supports both async and sync database operations.

Usage:
    from backend.db import get_session, engine
    
    # In sync context
    session = get_session()
    user = session.query(User).first()
    session.close()
    
    # Or use context manager
    with get_session() as session:
        user = session.query(User).first()
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
# For SQLite: no connection pooling needed
# For PostgreSQL: use pool_pre_ping and connection pooling
if settings.db_url.startswith("sqlite"):
    # SQLite configuration (development/testing)
    engine = create_engine(
        settings.db_url,
        connect_args={"check_same_thread": False},
        echo=settings.debug,
    )
else:
    # PostgreSQL configuration (production)
    engine = create_engine(
        settings.db_url,
        pool_pre_ping=True,
        echo=settings.debug,
        pool_size=20,
        max_overflow=40,
    )

# Session factory for creating new database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

logger.info(f"Database engine created: {settings.environment}")
logger.info(f"Using database: {settings.db_url.split('/')[-1]}")


def get_session() -> Generator[Session, None, None]:
    """
    Get a database session for dependency injection in FastAPI routes.
    
    Yields:
        Session: SQLAlchemy session
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_session)):
            return db.query(User).all()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def close_db():
    """Close database connection pool."""
    engine.dispose()
    logger.info("Database connections closed")
