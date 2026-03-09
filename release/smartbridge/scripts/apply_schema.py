#!/usr/bin/env python
"""
Apply Database Schema to PostgreSQL

Reads the SQL DDL from infra/sql/schema.sql and applies it to a PostgreSQL database.

Features:
- Reads schema from infra/sql/schema.sql
- Connects to PostgreSQL via SQLAlchemy
- Creates all tables, indexes, constraints, and views
- Validates connection before applying schema
- Skips if tables already exist (idempotent with IF NOT EXISTS)
- Logs all operations

Usage:
    python scripts/apply_schema.py
    python scripts/apply_schema.py --db-url postgresql://user:pass@localhost:5432/dbname
    python scripts/apply_schema.py --db-url postgresql://postgres:postgres@localhost:5432/ai_advisor_dev

Environment:
    DATABASE_URL - PostgreSQL connection URL (fallback if --db-url not provided)

Safety:
    - Prompts before applying schema if not in dev/localhost environment
    - Supports --force flag to bypass confirmation
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_schema_sql() -> str:
    """Read SQL schema from infra/sql/schema.sql.

    Returns:
        SQL DDL statements as string

    Raises:
        FileNotFoundError: If schema.sql does not exist
    """
    # Try multiple paths to find schema.sql
    possible_paths = [
        Path(__file__).parent.parent / "infra" / "sql" / "schema.sql",
        Path("infra/sql/schema.sql"),
        Path("./infra/sql/schema.sql"),
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Found schema at: {path}")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

    raise FileNotFoundError(
        f"schema.sql not found. Searched: {[str(p) for p in possible_paths]}"
    )


def validate_connection(engine) -> bool:
    """Test database connection.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        True if connection successful

    Raises:
        SQLAlchemyError: If connection fails
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
            return True
    except SQLAlchemyError as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise


def get_existing_tables(engine) -> set:
    """Get list of existing tables in database.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        Set of table names
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    logger.info(f"Found {len(tables)} existing tables: {tables}")
    return tables


def is_dev_environment(db_url: str) -> bool:
    """Check if database is in dev/localhost environment.

    Args:
        db_url: PostgreSQL connection URL

    Returns:
        True if localhost or '.dev' in hostname
    """
    # Parse hostname from URL
    if "localhost" in db_url or "127.0.0.1" in db_url or ".dev" in db_url:
        return True
    return False


def apply_schema(db_url: str, force: bool = False) -> dict:
    """Apply database schema to PostgreSQL.

    Args:
        db_url: PostgreSQL connection URL
        force: Skip safety prompts if True

    Returns:
        Dictionary with operation summary

    Raises:
        ValueError: If database URL is invalid
        SQLAlchemyError: If SQL execution fails
    """
    if not db_url:
        raise ValueError("Database URL not provided")

    logger.info(f"Target database: {db_url}")

    # Safety check: warn if not dev environment
    if not is_dev_environment(db_url) and not force:
        logger.warning("\n⚠️  WARNING: This database does not appear to be local development!")
        logger.warning(f"   Database URL: {db_url}")
        response = input(
            "\nContinue applying schema? Type 'yes' to confirm: "
        ).strip().lower()
        if response != "yes":
            logger.info("Schema application cancelled")
            return {"status": "cancelled", "reason": "User declined"}

    # Create engine
    try:
        engine = create_engine(db_url, echo=False)
        logger.info("✓ SQLAlchemy engine created")
    except Exception as e:
        logger.error(f"✗ Failed to create engine: {e}")
        raise

    # Validate connection
    validate_connection(engine)

    # Get existing tables
    existing_tables = get_existing_tables(engine)

    # Read schema
    try:
        schema_sql = get_schema_sql()
        logger.info(f"✓ Read schema SQL ({len(schema_sql)} characters)")
    except FileNotFoundError as e:
        logger.error(f"✗ {e}")
        raise

    # Apply schema
    results = {
        "status": "success",
        "tables_created": [],
        "views_created": [],
        "errors": [],
    }

    try:
        with engine.begin() as conn:
            # Split by semicolons and execute each statement
            statements = [
                stmt.strip()
                for stmt in schema_sql.split(";")
                if stmt.strip() and not stmt.strip().startswith("--")
            ]

            for i, statement in enumerate(statements, 1):
                if not statement:
                    continue

                try:
                    logger.info(f"Executing statement {i}/{len(statements)}...")
                    conn.execute(text(statement))
                except SQLAlchemyError as e:
                    # Some statements might fail if objects already exist (due to IF EXISTS)
                    # This is expected and not an error
                    if "already exists" not in str(e) and "duplicate" not in str(e):
                        logger.warning(f"Statement {i} warning: {str(e)[:100]}")
                        results["errors"].append(
                            {
                                "statement": statement[:100],
                                "error": str(e)[:200],
                            }
                        )

            logger.info("✓ Schema applied successfully")

    except Exception as e:
        logger.error(f"✗ Failed to apply schema: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        raise

    # Verify tables
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        new_tables = tables - existing_tables

        logger.info(f"\n✓ Schema application results:")
        logger.info(f"  Total tables: {len(tables)}")
        logger.info(f"  New tables: {len(new_tables)}")
        logger.info(f"  Tables: {', '.join(sorted(tables))}")

        results["tables_created"] = sorted(new_tables)

        # Check for views
        views = inspector.get_view_names()
        if views:
            logger.info(f"  Views created: {len(views)}")
            logger.info(f"  Views: {', '.join(views)}")
            results["views_created"] = views

    except Exception as e:
        logger.error(f"✗ Failed to verify schema: {e}")

    return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Apply database schema to PostgreSQL"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="PostgreSQL connection URL (or use DATABASE_URL environment variable)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip safety confirmations for non-dev databases",
    )

    args = parser.parse_args()

    # Get database URL
    db_url = args.db_url or os.getenv("DATABASE_URL")

    if not db_url:
        logger.error("\n✗ Error: Database URL not provided")
        logger.error("  Provide via --db-url or DATABASE_URL environment variable")
        logger.error("\n  Example:")
        logger.error("    python scripts/apply_schema.py \\")
        logger.error("      --db-url postgresql://postgres:postgres@localhost:5432/ai_advisor_dev")
        exit(1)

    try:
        results = apply_schema(db_url, force=args.force)

        # Print summary
        print("\n" + "=" * 70)
        print("DATABASE SCHEMA APPLICATION")
        print("=" * 70)
        print(f"Status:                {results.get('status', 'unknown')}")
        print(f"Tables created:        {', '.join(results.get('tables_created', []))}")
        print(f"Views created:         {', '.join(results.get('views_created', []))}")
        if results.get("errors"):
            print(f"Warnings/Errors:       {len(results['errors'])}")
        print("=" * 70 + "\n")

        exit(0)

    except Exception as e:
        logger.error(f"\n✗ Schema application failed: {e}")
        print("\n" + "=" * 70)
        print("ERROR")
        print("=" * 70)
        print(f"Failed to apply schema: {str(e)}")
        print("=" * 70 + "\n")
        exit(1)


if __name__ == "__main__":
    main()
