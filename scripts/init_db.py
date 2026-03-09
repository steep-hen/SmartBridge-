#!/usr/bin/env python
"""
Initialize the SQLite database with schema and sample data.

Run this script once to set up the database:
    python scripts/init_db.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import engine
from backend.models import Base
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """Create all tables in the database."""
    logger.info("Initializing database...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
        
        # Try to create demo user as well
        from backend.models import User
        session = Session(engine)
        
        # Check if demo user already exists
        demo_user = session.query(User).filter(
            User.email == "demo@smartbridge.com"
        ).first()
        
        if not demo_user:
            # Create demo user
            demo_user = User(
                email="demo@smartbridge.com",
                name="Demo User",
                country="USA",
            )
            session.add(demo_user)
            session.commit()
            logger.info(f"✅ Demo user created: {demo_user.email}")
        else:
            logger.info("ℹ️  Demo user already exists")
        
        session.close()
        logger.info("✅ Database initialization complete!")
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    init_database()
