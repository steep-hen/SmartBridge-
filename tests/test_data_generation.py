"""
Tests for Synthetic Data Generation

Validates that the synthetic data generator produces correct outputs:
- All expected CSV files created
- Correct row counts and structure
- Proper data types and formats
- Deterministic output with seeding
"""

import os
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd

# Adjust import path for running tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.generate_synthetic_data import SyntheticDataGenerator


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestSyntheticDataGenerator:
    """Test suite for SyntheticDataGenerator."""

    def test_generator_initialization(self):
        """Test that generator initializes with correct parameters."""
        gen = SyntheticDataGenerator(n_users=10, months=6, seed=42)
        assert gen.n_users == 10
        assert gen.months == 6
        assert gen.seed == 42

    def test_generate_users(self, temp_data_dir):
        """Test user generation."""
        gen = SyntheticDataGenerator(n_users=10, months=6, seed=42)
        users = gen.generate_users()

        assert len(users) == 10, "Should generate exactly n_users records"
        
        # Check required fields
        required_fields = ["id", "email", "name"]
        for user in users:
            for field in required_fields:
                assert field in user, f"User missing field: {field}"
                assert user[field] is not None, f"Required field {field} is None"

        # Check email uniqueness
        emails = [u["email"] for u in users]
        assert len(set(emails)) == len(emails), "Emails should be unique"

    def test_generate_transactions(self, temp_data_dir):
        """Test transaction generation."""
        gen = SyntheticDataGenerator(n_users=5, months=3, seed=42)
        users = gen.generate_users()
        transactions = gen.generate_transactions(users)

        # Expect roughly 20-40 transactions per user per month
        expected_min = 5 * 3 * 20  # 300
        expected_max = 5 * 3 * 40  # 600
        assert expected_min <= len(transactions) <= expected_max, \
            f"Transaction count {len(transactions)} outside range [{expected_min}, {expected_max}]"

        # Check required fields
        required_fields = ["id", "user_id", "transaction_date", "amount", "category"]
        for txn in transactions:
            for field in required_fields:
                assert field in txn, f"Transaction missing field: {field}"
                assert txn[field] is not None, f"Required field {field} is None"

            # Validate amount value
            assert float(txn["amount"]) > 0, "Transaction amount must be positive"

            # Validate date format
            try:
                datetime.fromisoformat(str(txn["transaction_date"]))
            except ValueError:
                pytest.fail(f"Invalid date format: {txn['transaction_date']}")

    def test_generate_financial_summary(self, temp_data_dir):
        """Test financial summary generation."""
        gen = SyntheticDataGenerator(n_users=5, months=3, seed=42)
        users = gen.generate_users()
        summaries = gen.generate_financial_summary(users)

        # Should have one record per user per month
        expected_count = 5 * 3
        assert len(summaries) == expected_count, \
            f"Should have {expected_count} summaries (users × months)"

        # Check required fields
        required_fields = ["id", "user_id", "year", "month", "total_income"]
        for summary in summaries:
            for field in required_fields:
                assert field in summary, f"Summary missing field: {field}"
                assert summary[field] is not None, f"Required field {field} is None"

    def test_generate_goals(self, temp_data_dir):
        """Test goal generation."""
        gen = SyntheticDataGenerator(n_users=10, months=6, seed=42)
        users = gen.generate_users()
        goals = gen.generate_goals(users)

        # Should have 2-5 goals per user
        assert 10 * 2 <= len(goals) <= 10 * 5, \
            f"Goal count {len(goals)} not in expected range [{10*2}, {10*5}]"

        # Check required fields
        required_fields = ["id", "user_id", "goal_name", "target_amount"]
        for goal in goals:
            for field in required_fields:
                assert field in goal, f"Goal missing field: {field}"
                assert goal[field] is not None, f"Required field {field} is None"

            # Validate amount
            assert float(goal["target_amount"]) > 0, "Goal target_amount must be positive"

    def test_generate_holdings(self, temp_data_dir):
        """Test holdings generation."""
        gen = SyntheticDataGenerator(n_users=10, months=6, seed=42)
        users = gen.generate_users()
        holdings = gen.generate_holdings(users)

        # Should have 1-5 holdings per user
        assert 10 * 1 <= len(holdings) <= 10 * 5, \
            f"Holdings count {len(holdings)} not in expected range [{10*1}, {10*5}]"

        # Check required fields
        required_fields = ["id", "user_id", "ticker", "quantity", "average_cost"]
        for holding in holdings:
            for field in required_fields:
                assert field in holding, f"Holding missing field: {field}"
                assert holding[field] is not None, f"Required field {field} is None"

            # Validate amounts
            assert float(holding["quantity"]) > 0, "Quantity must be positive"
            assert float(holding["average_cost"]) > 0, "Cost must be positive"

    def test_generate_market_prices(self, temp_data_dir):
        """Test market price generation."""
        gen = SyntheticDataGenerator(n_users=10, months=3, seed=42)
        prices = gen.generate_market_prices()

        # Should have prices for multiple tickers across multiple dates
        # 5 tickers × ~60 trading days in 3 months = ~300 records
        assert len(prices) > 200, f"Expected >200 price records, got {len(prices)}"

        # Check required fields
        required_fields = ["id", "ticker", "price_date", "open_price", "close_price"]
        for price in prices:
            for field in required_fields:
                assert field in price, f"Price record missing field: {field}"
                assert price[field] is not None, f"Required field {field} is None"

            # Validate prices
            assert float(price["open_price"]) > 0, "Open price must be positive"
            assert float(price["close_price"]) > 0, "Close price must be positive"

    def test_deterministic_generation(self, temp_data_dir):
        """Test that same seed produces identical data."""
        # Generate twice with same seed
        gen1 = SyntheticDataGenerator(n_users=10, months=3, seed=123)
        users1 = gen1.generate_users()
        transactions1 = gen1.generate_transactions(users1)

        gen2 = SyntheticDataGenerator(n_users=10, months=3, seed=123)
        users2 = gen2.generate_users()
        transactions2 = gen2.generate_transactions(users2)

        # Should have identical data
        assert len(users1) == len(users2)
        assert len(transactions1) == len(transactions2)

        # Check that email sequences are identical
        emails1 = sorted([u["email"] for u in users1])
        emails2 = sorted([u["email"] for u in users2])
        assert emails1 == emails2, "Same seed should produce identical user emails"

    def test_save_to_csv(self, temp_data_dir):
        """Test saving generated data to CSV files."""
        gen = SyntheticDataGenerator(n_users=10, months=3, seed=42, out_dir=temp_data_dir)
        result = gen.save_to_csv()

        # Check that all expected CSV files were created
        expected_files = [
            "users.csv",
            "transactions.csv",
            "financial_summary.csv",
            "goals.csv",
            "holdings.csv",
            "market_prices.csv",
        ]
        
        for filename in expected_files:
            filepath = Path(temp_data_dir) / filename
            assert filepath.exists(), f"Expected file not created: {filename}"

        # Verify file contents
        users_df = pd.read_csv(Path(temp_data_dir) / "users.csv")
        assert len(users_df) == 10, "users.csv should have 10 rows"
        assert "id" in users_df.columns
        assert "email" in users_df.columns

        transactions_df = pd.read_csv(Path(temp_data_dir) / "transactions.csv")
        assert len(transactions_df) > 0, "transactions.csv should have data"
        assert all(transactions_df["amount"] > 0), "All transaction amounts should be positive"

    def test_csv_structure_and_columns(self, temp_data_dir):
        """Test that CSV files have correct structure and columns."""
        gen = SyntheticDataGenerator(n_users=5, months=2, seed=42, out_dir=temp_data_dir)
        gen.save_to_csv()

        # Define expected columns for each CSV
        expected_columns = {
            "users.csv": ["id", "email", "name", "phone", "date_of_birth", "gender", "country"],
            "transactions.csv": ["id", "user_id", "transaction_date", "amount", "category"],
            "goals.csv": ["id", "user_id", "goal_name", "target_amount"],
            "holdings.csv": ["id", "user_id", "ticker", "quantity", "average_cost"],
            "market_prices.csv": ["id", "ticker", "price_date", "open_price", "close_price"],
        }

        for filename, expected_cols in expected_columns.items():
            filepath = Path(temp_data_dir) / filename
            df = pd.read_csv(filepath)
            
            for col in expected_cols:
                assert col in df.columns, f"{filename} missing column: {col}"

    def test_no_negative_amounts(self, temp_data_dir):
        """Test that generator doesn't produce negative amounts."""
        gen = SyntheticDataGenerator(n_users=10, months=6, seed=42, out_dir=temp_data_dir)
        gen.save_to_csv()

        # Check transactions
        transactions_df = pd.read_csv(Path(temp_data_dir) / "transactions.csv")
        assert (transactions_df["amount"] > 0).all(), "All transaction amounts must be positive"

        # Check goals
        goals_df = pd.read_csv(Path(temp_data_dir) / "goals.csv")
        assert (goals_df["target_amount"] > 0).all(), "All goal amounts must be positive"

        # Check holdings
        holdings_df = pd.read_csv(Path(temp_data_dir) / "holdings.csv")
        assert (holdings_df["quantity"] > 0).all(), "All quantities must be positive"
        assert (holdings_df["average_cost"] > 0).all(), "All costs must be positive"

    def test_date_validity(self, temp_data_dir):
        """Test that all dates are valid."""
        gen = SyntheticDataGenerator(n_users=5, months=3, seed=42, out_dir=temp_data_dir)
        gen.save_to_csv()

        # Check transaction dates
        transactions_df = pd.read_csv(Path(temp_data_dir) / "transactions.csv")
        try:
            pd.to_datetime(transactions_df["transaction_date"])
        except Exception as e:
            pytest.fail(f"Invalid date in transactions: {e}")

        # Check market price dates
        prices_df = pd.read_csv(Path(temp_data_dir) / "market_prices.csv")
        try:
            pd.to_datetime(prices_df["price_date"])
        except Exception as e:
            pytest.fail(f"Invalid date in market prices: {e}")

    def test_foreign_key_consistency(self, temp_data_dir):
        """Test that foreign keys reference valid parent records."""
        gen = SyntheticDataGenerator(n_users=10, months=3, seed=42, out_dir=temp_data_dir)
        gen.save_to_csv()

        users_df = pd.read_csv(Path(temp_data_dir) / "users.csv")
        valid_user_ids = set(users_df["id"])

        # Check transactions reference valid users
        transactions_df = pd.read_csv(Path(temp_data_dir) / "transactions.csv")
        invalid_users = set(transactions_df["user_id"]) - valid_user_ids
        assert len(invalid_users) == 0, f"Found invalid user references in transactions: {invalid_users}"

        # Check goals reference valid users
        goals_df = pd.read_csv(Path(temp_data_dir) / "goals.csv")
        invalid_users = set(goals_df["user_id"]) - valid_user_ids
        assert len(invalid_users) == 0, f"Found invalid user references in goals: {invalid_users}"

        # Check holdings reference valid users
        holdings_df = pd.read_csv(Path(temp_data_dir) / "holdings.csv")
        invalid_users = set(holdings_df["user_id"]) - valid_user_ids
        assert len(invalid_users) == 0, f"Found invalid user references in holdings: {invalid_users}"


class TestDataGenerationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_user(self, temp_data_dir):
        """Test generation with single user."""
        gen = SyntheticDataGenerator(n_users=1, months=1, seed=42, out_dir=temp_data_dir)
        gen.save_to_csv()

        users_df = pd.read_csv(Path(temp_data_dir) / "users.csv")
        assert len(users_df) == 1

    def test_large_dataset(self, temp_data_dir):
        """Test generation with larger dataset."""
        gen = SyntheticDataGenerator(n_users=100, months=12, seed=42, out_dir=temp_data_dir)
        gen.save_to_csv()

        users_df = pd.read_csv(Path(temp_data_dir) / "users.csv")
        assert len(users_df) == 100

        transactions_df = pd.read_csv(Path(temp_data_dir) / "transactions.csv")
        assert len(transactions_df) > 0

    def test_different_locales(self):
        """Test generator with different locales."""
        for locale in ["en_US", "en_GB", "de_DE"]:
            gen = SyntheticDataGenerator(n_users=5, months=1, seed=42, locale=locale)
            users = gen.generate_users()
            assert len(users) == 5
            # All users should have names
            assert all(u["name"] for u in users)

    def test_custom_output_directory(self):
        """Test saving to custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_data"
            gen = SyntheticDataGenerator(
                n_users=5, months=1, seed=42, out_dir=str(custom_dir)
            )
            gen.save_to_csv()

            assert custom_dir.exists()
            assert (custom_dir / "users.csv").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
