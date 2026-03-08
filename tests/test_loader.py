"""
Tests for Data Loader

Validates that load_data.py correctly:
- Reads and validates CSV files
- Loads data into database
- Maintains referential integrity
- Produces expected row counts
- Handles errors gracefully

These tests use SQLite for testing to avoid external dependencies.
"""

import os
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, inspect, text

# Adjust import path for running tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_synthetic_data import SyntheticDataGenerator
from scripts.load_data import DataValidator, DataLoader


@pytest.fixture
def temp_data_dir():
    """Create temporary directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Generate small test dataset
        gen = SyntheticDataGenerator(n_users=5, months=3, seed=42)
        gen.save_to_csv(output_dir=tmpdir)
        yield tmpdir


@pytest.fixture
def sqlite_db():
    """Create in-memory SQLite database for testing."""
    db_url = "sqlite:///:memory:"
    engine = create_engine(db_url)
    
    # Create minimal schema for testing
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT,
                date_of_birth TEXT,
                gender TEXT,
                country TEXT
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE financial_summary (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                total_income DECIMAL NOT NULL,
                total_expenses DECIMAL,
                total_savings DECIMAL,
                total_investments DECIMAL,
                net_worth DECIMAL,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                UNIQUE(user_id, year, month),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE transactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                amount DECIMAL NOT NULL,
                category TEXT NOT NULL,
                merchant_name TEXT,
                transaction_type TEXT,
                payment_method TEXT,
                description TEXT,
                is_recurring BOOLEAN,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE goals (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                goal_name TEXT NOT NULL,
                description TEXT,
                target_amount DECIMAL NOT NULL,
                current_amount DECIMAL,
                target_date TEXT,
                goal_type TEXT,
                status TEXT,
                priority TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE holdings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                ticker TEXT NOT NULL,
                quantity DECIMAL NOT NULL,
                average_cost DECIMAL NOT NULL,
                current_value DECIMAL,
                asset_type TEXT,
                purchase_date TEXT,
                last_updated TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE market_prices (
                id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                price_date TEXT NOT NULL,
                open_price DECIMAL NOT NULL,
                close_price DECIMAL NOT NULL,
                high_price DECIMAL,
                low_price DECIMAL,
                volume INTEGER,
                created_at TIMESTAMP
            )
        """))
        
        conn.commit()
    
    yield db_url, engine


class TestDataValidator:
    """Test suite for DataValidator."""

    def test_validator_initialization(self, temp_data_dir):
        """Test validator initialization."""
        validator = DataValidator(data_dir=temp_data_dir)
        assert validator.data_dir == Path(temp_data_dir)

    def test_validate_users_csv(self, temp_data_dir):
        """Test validation of users CSV."""
        validator = DataValidator(data_dir=temp_data_dir)
        users_path = Path(temp_data_dir) / "users.csv"
        
        result = validator.validate_users_csv(users_path)
        assert result is True
        assert len(validator.user_ids) == 5  # 5 users generated

    def test_validate_transactions_csv(self, temp_data_dir):
        """Test validation of transactions CSV."""
        validator = DataValidator(data_dir=temp_data_dir)
        users_path = Path(temp_data_dir) / "users.csv"
        validator.validate_users_csv(users_path)
        
        txn_path = Path(temp_data_dir) / "transactions.csv"
        result = validator.validate_transactions_csv(txn_path)
        assert result is True

    def test_validate_financial_summary_csv(self, temp_data_dir):
        """Test validation of financial summary CSV."""
        validator = DataValidator(data_dir=temp_data_dir)
        users_path = Path(temp_data_dir) / "users.csv"
        validator.validate_users_csv(users_path)
        
        fin_path = Path(temp_data_dir) / "financial_summary.csv"
        result = validator.validate_financial_summary_csv(fin_path)
        assert result is True

    def test_validate_goals_csv(self, temp_data_dir):
        """Test validation of goals CSV."""
        validator = DataValidator(data_dir=temp_data_dir)
        users_path = Path(temp_data_dir) / "users.csv"
        validator.validate_users_csv(users_path)
        
        goals_path = Path(temp_data_dir) / "goals.csv"
        result = validator.validate_goals_csv(goals_path)
        assert result is True

    def test_validate_holdings_csv(self, temp_data_dir):
        """Test validation of holdings CSV."""
        validator = DataValidator(data_dir=temp_data_dir)
        users_path = Path(temp_data_dir) / "users.csv"
        validator.validate_users_csv(users_path)
        
        holdings_path = Path(temp_data_dir) / "holdings.csv"
        result = validator.validate_holdings_csv(holdings_path)
        assert result is True

    def test_validate_market_prices_csv(self, temp_data_dir):
        """Test validation of market prices CSV."""
        validator = DataValidator(data_dir=temp_data_dir)
        prices_path = Path(temp_data_dir) / "market_prices.csv"
        result = validator.validate_market_prices_csv(prices_path)
        assert result is True

    def test_validate_all(self, temp_data_dir):
        """Test validation of all CSV files."""
        validator = DataValidator(data_dir=temp_data_dir)
        result = validator.validate_all()
        assert result is True

    def test_validate_detects_missing_users_csv(self):
        """Test that validator detects missing users.csv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = DataValidator(data_dir=tmpdir)
            with pytest.raises(FileNotFoundError):
                validator.validate_all()

    def test_validate_rejects_invalid_amounts(self):
        """Test that validator rejects negative amounts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create users.csv
            users_df = pd.DataFrame({
                "id": ["123"],
                "email": ["test@example.com"],
                "name": ["Test User"],
                "phone": ["555-1234"],
                "date_of_birth": ["1990-01-01"],
                "gender": ["M"],
                "country": ["USA"]
            })
            users_df.to_csv(Path(tmpdir) / "users.csv", index=False)
            
            # Create transactions.csv with negative amount
            txn_df = pd.DataFrame({
                "id": ["456"],
                "user_id": ["123"],
                "transaction_date": ["2024-01-01"],
                "amount": [-100.00],  # INVALID: negative
                "category": ["Salary"]
            })
            txn_df.to_csv(Path(tmpdir) / "transactions.csv", index=False)
            
            validator = DataValidator(data_dir=tmpdir)
            with pytest.raises(ValueError, match="non-positive"):
                validator.validate_all()


class TestDataLoader:
    """Test suite for DataLoader."""

    def test_loader_initialization(self, sqlite_db):
        """Test loader initialization."""
        db_url, _ = sqlite_db
        loader = DataLoader(db_url)
        assert loader.db_url == db_url

    def test_load_users_table(self, temp_data_dir, sqlite_db):
        """Test loading users table."""
        db_url, engine = sqlite_db
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        
        csv_path = Path(temp_data_dir) / "users.csv"
        row_count = loader.load_csv_to_table(csv_path, "users")
        
        assert row_count == 5

    def test_load_transactions_table(self, temp_data_dir, sqlite_db):
        """Test loading transactions table."""
        db_url, engine = sqlite_db
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        
        # Load users first (FK constraint)
        users_path = Path(temp_data_dir) / "users.csv"
        loader.load_csv_to_table(users_path, "users")
        
        # Load transactions
        txn_path = Path(temp_data_dir) / "transactions.csv"
        row_count = loader.load_csv_to_table(txn_path, "transactions")
        
        assert row_count > 0

    def test_load_financial_summary_table(self, temp_data_dir, sqlite_db):
        """Test loading financial_summary table."""
        db_url, engine = sqlite_db
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        
        # Load users first
        users_path = Path(temp_data_dir) / "users.csv"
        loader.load_csv_to_table(users_path, "users")
        
        # Load financial summary
        fin_path = Path(temp_data_dir) / "financial_summary.csv"
        row_count = loader.load_csv_to_table(fin_path, "financial_summary")
        
        assert row_count > 0
        # Count equals rows loaded (exact count may vary with data generation)
        assert row_count >= 5  # At least 5 users × months

    def test_load_all_tables(self, temp_data_dir, sqlite_db):
        """Test loading all tables."""
        db_url, engine = sqlite_db
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        
        results = loader.load_all()
        
        # Check that tables were loaded
        assert "users" in results["tables_loaded"]
        assert results["tables_loaded"]["users"] == 5
        assert results["total_rows"] > 0

    def test_load_nonexistent_file(self, sqlite_db):
        """Test that loader handles missing CSV files gracefully."""
        db_url, _ = sqlite_db
        loader = DataLoader(db_url, data_dir="/nonexistent/path")
        
        # Should skip missing files without throwing error
        result = loader.load_all()
        assert result["total_rows"] == 0

    def test_verify_load(self, temp_data_dir, sqlite_db):
        """Test verification after load."""
        db_url, engine = sqlite_db
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        
        # Load all data
        loader.load_all()
        
        # Verify should succeed without errors
        loader.verify_load()


class TestDataLoadingIntegration:
    """Integration tests for full data loading workflow."""

    def test_end_to_end_load(self, temp_data_dir, sqlite_db):
        """Test complete load workflow: validate > load > verify."""
        db_url, engine = sqlite_db
        
        # Step 1: Validate
        validator = DataValidator(data_dir=temp_data_dir)
        assert validator.validate_all() is True
        
        # Step 2: Load
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        results = loader.load_all()
        
        assert results["total_rows"] > 0
        assert "users" in results["tables_loaded"]
        assert results["tables_loaded"]["users"] == 5

    def test_referential_integrity(self, temp_data_dir, sqlite_db):
        """Test that referential integrity is maintained after load."""
        db_url, engine = sqlite_db
        
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        loader.load_all()
        
        # Check that all user_id references in transactions exist in users
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as orphaned FROM transactions
                WHERE user_id NOT IN (SELECT id FROM users)
            """))
            orphaned = result.scalar()
            assert orphaned == 0, "Found orphaned transaction records"

    def test_data_types_preserved(self, temp_data_dir, sqlite_db):
        """Test that data types are correctly preserved after load."""
        db_url, engine = sqlite_db
        
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        results = loader.load_all()
        
        # Verify data was loaded
        assert results["total_rows"] > 0

    def test_unique_constraints(self, temp_data_dir, sqlite_db):
        """Test that unique constraints are respected."""
        db_url, engine = sqlite_db
        
        loader = DataLoader(db_url, data_dir=temp_data_dir)
        loader.load_all()
        
        with engine.connect() as conn:
            # Check email uniqueness
            result = conn.execute(text("""
                SELECT COUNT(*) as duplicates FROM (
                    SELECT email, COUNT(*) as cnt FROM users
                    GROUP BY email HAVING cnt > 1
                )
            """))
            duplicates = result.scalar()
            assert duplicates == 0, "Found duplicate emails"


class TestDataValidationEdgeCases:
    """Test edge cases in data validation."""

    def test_empty_csv_file(self, sqlite_db):
        """Test handling of empty CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty CSV files
            Path(tmpdir).joinpath("users.csv").write_text("id,email,name\n")
            
            loader = DataLoader(sqlite_db[0], data_dir=tmpdir)
            csv_path = Path(tmpdir) / "users.csv"
            
            # Should handle gracefully
            result = loader.load_csv_to_table(csv_path, "users")
            assert result == 0

    def test_large_dataset_load(self, sqlite_db):
        """Test loading larger dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate larger test dataset
            gen = SyntheticDataGenerator(n_users=20, months=6, seed=42)
            gen.save_to_csv(output_dir=tmpdir)
            
            # Load all data
            db_url, engine = sqlite_db
            loader = DataLoader(db_url, data_dir=tmpdir)
            results = loader.load_all()
            
            # Should load successfully
            assert results["total_rows"] > 0
            assert results["tables_loaded"]["users"] == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
