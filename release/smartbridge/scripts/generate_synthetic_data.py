#!/usr/bin/env python
"""
Synthetic Financial Data Generator

Generates realistic financial data for AI Financial Advisor testing and development.

Features:
- Deterministic data generation (reproducible with seed)
- Realistic transaction patterns (recurring bills, random expenses)
- Market price series with random walk
- Multiple locale support (en_US, en_IN, en_GB, de_DE, es_ES)
- Configurable user count, time period, and output directory

Usage:
    python scripts/generate_synthetic_data.py --n-users 100 --months 36 --seed 42
    python scripts/generate_synthetic_data.py --n-users 500 --months 12 --seed 123 --locale en_IN
    python scripts/generate_synthetic_data.py --out-dir /tmp/data/

Example:
    python scripts/generate_synthetic_data.py \\
        --n-users 100 \\
        --months 24 \\
        --seed 42 \\
        --locale en_IN \\
        --out-dir data/
"""

import argparse
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple
import random

try:
    from faker import Faker
    import numpy as np
except ImportError:
    print("Error: Required packages not installed.")
    print("Install with: pip install faker numpy")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
TRANSACTION_CATEGORIES = {
    "Salary": {"type": "INCOME", "min": 40000, "max": 150000, "recurring": "monthly"},
    "Rent": {"type": "EXPENSE", "min": 10000, "max": 50000, "recurring": "monthly"},
    "Utilities": {
        "type": "EXPENSE",
        "min": 1000,
        "max": 5000,
        "recurring": "monthly",
    },
    "Groceries": {"type": "EXPENSE", "min": 2000, "max": 8000, "recurring": "weekly"},
    "Transport": {"type": "EXPENSE", "min": 500, "max": 3000, "recurring": "variable"},
    "Entertainment": {
        "type": "EXPENSE",
        "min": 500,
        "max": 5000,
        "recurring": "variable",
    },
    "Loan Payment": {
        "type": "EXPENSE",
        "min": 5000,
        "max": 30000,
        "recurring": "monthly",
    },
    "Investment": {
        "type": "INVESTMENT",
        "min": 5000,
        "max": 50000,
        "recurring": "variable",
    },
    "Insurance": {
        "type": "EXPENSE",
        "min": 1000,
        "max": 10000,
        "recurring": "monthly",
    },
    "Healthcare": {"type": "EXPENSE", "min": 500, "max": 10000, "recurring": "variable"},
    "Online Shopping": {
        "type": "EXPENSE",
        "min": 500,
        "max": 10000,
        "recurring": "variable",
    },
    "Dining": {"type": "EXPENSE", "min": 300, "max": 3000, "recurring": "variable"},
}

AVAILABLE_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
ASSET_TYPES = ["EQUITY", "MUTUAL_FUND", "BOND"]
GOAL_TYPES = [
    "SAVINGS",
    "INVESTMENT",
    "DEBT_PAYOFF",
    "EDUCATION",
    "HOME",
    "RETIREMENT",
]
PRIORITIES = ["LOW", "MEDIUM", "HIGH"]

MERCHANTS = {
    "Salary": ["Employer Payroll", "Salary Direct Deposit"],
    "Rent": ["Landlord - Direct Transfer", "Property Management"],
    "Utilities": ["Electric Company", "Water Board", "Internet Provider"],
    "Groceries": [
        "BigMart Supermarket",
        "Fresh Foods Market",
        "Online Grocery Store",
    ],
    "Transport": [
        "Uber",
        "Local Taxi Service",
        "Gas Station",
        "Metro Pass",
        "Parking",
    ],
    "Entertainment": [
        "Netflix Subscription",
        "Cinema Hall",
        "Concert Tickets",
        "Gaming Store",
    ],
    "Loan Payment": ["Bank - Loan EMI", "Loan Servicer"],
    "Investment": ["Stock Broker", "Mutual Fund Provider", "Investment App"],
    "Insurance": ["Insurance Company", "Broker Insurance"],
    "Healthcare": [
        "Hospital",
        "Pharmacy",
        "Clinic",
        "Medical Lab",
        "Dental Center",
    ],
    "Online Shopping": ["Amazon", "Flipkart", "eBay", "Fashion Store Online"],
    "Dining": ["Restaurant", "Cafe", "Fast Food Chain", "Food Delivery App"],
}


class SyntheticDataGenerator:
    """Generate realistic synthetic financial data."""

    def __init__(self, n_users: int = 100, months: int = 36, seed: int = 42,
                 locale: str = "en_US"):
        """Initialize generator with parameters.

        Args:
            n_users: Number of users to generate
            months: Number of months of data (affects transaction count)
            seed: Random seed for reproducibility
            locale: Faker locale code (en_US, en_IN, de_DE, es_ES, en_GB)
        """
        self.n_users = n_users
        self.months = months
        self.seed = seed
        self.locale = locale

        # Set seeds for reproducibility
        random.seed(seed)
        np.random.seed(seed)

        # Initialize Faker with seed
        self.faker = Faker(locale=locale)
        self.faker.seed_instance(seed)

        # Pre-generate date range
        self.end_date = datetime.now().replace(day=1) - timedelta(days=1)
        self.start_date = self.end_date - timedelta(days=30 * months)

        logger.info(
            f"Generator initialized: {n_users} users, {months} months, "
            f"seed={seed}, locale={locale}"
        )

    def generate_users(self) -> List[dict]:
        """Generate user records.

        Returns:
            List of user dictionaries with: id, email, name, phone, dob, gender, country

        Example row:
            {
                'id': '550e8400-e29b-41d4-a716-446655440000',
                'email': 'john.doe@example.com',
                'name': 'John Doe',
                'phone': '+1-555-123-4567',
                'date_of_birth': '1990-05-15',
                'gender': 'M',
                'country': 'United States'
            }
        """
        users = []
        for i in range(self.n_users):
            user = {
                "id": self.faker.uuid4(),
                "email": self.faker.email(),
                "name": self.faker.name(),
                "phone": self.faker.phone_number(),
                "date_of_birth": self.faker.date_of_birth(
                    minimum_age=18, maximum_age=70
                ).isoformat(),
                "gender": random.choice(["M", "F", "O"]),
                "country": self.faker.country(),
            }
            users.append(user)

        logger.info(f"Generated {len(users)} users")
        return users

    def generate_financial_summary(self, users: List[dict]) -> List[dict]:
        """Generate monthly financial summaries for each user.

        Returns:
            List of financial_summary dictionaries

        Example row:
            {
                'id': '550e8400-e29b-41d4-a716-446655440001',
                'user_id': '550e8400-e29b-41d4-a716-446655440000',
                'year': 2024,
                'month': 3,
                'total_income': 95000.00,
                'total_expenses': 67500.00,
                'total_savings': 27500.00,
                'total_investments': 15000.00,
                'net_worth': 450000.00
            }
        """
        summaries = []
        current_date = self.start_date

        while current_date <= self.end_date:
            month_start = current_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(
                days=1
            )

            for user in users:
                # Realistic income/expense ranges
                monthly_income = round(
                    random.uniform(40000, 150000), 2
                )  # Salary, other income
                monthly_expenses = round(
                    random.uniform(20000, 100000), 2
                )  # Variable spending
                monthly_savings = round(
                    max(0, monthly_income - monthly_expenses), 2
                )
                monthly_investments = round(
                    random.uniform(5000, 40000), 2
                )  # Monthly investment
                net_worth = round(
                    random.uniform(200000, 5000000), 2
                )  # Accumulated wealth

                summary = {
                    "id": self.faker.uuid4(),
                    "user_id": user["id"],
                    "year": current_date.year,
                    "month": current_date.month,
                    "total_income": monthly_income,
                    "total_expenses": monthly_expenses,
                    "total_savings": monthly_savings,
                    "total_investments": monthly_investments,
                    "net_worth": net_worth,
                }
                summaries.append(summary)

            # Move to next month
            current_date = (current_date + timedelta(days=32)).replace(day=1) - timedelta(
                days=1
            )

        logger.info(f"Generated {len(summaries)} monthly financial summaries")
        return summaries

    def generate_transactions(self, users: List[dict]) -> List[dict]:
        """Generate transaction records (~30 per user per month).

        Returns:
            List of transaction dictionaries

        Example row:
            {
                'id': '550e8400-e29b-41d4-a716-446655440002',
                'user_id': '550e8400-e29b-41d4-a716-446655440000',
                'transaction_date': '2024-03-15',
                'amount': 2500.00,
                'category': 'Groceries',
                'description': 'Weekly grocery shopping',
                'merchant_name': 'BigMart Supermarket',
                'transaction_type': 'EXPENSE',
                'payment_method': 'CARD',
                'is_recurring': False
            }
        """
        transactions = []
        current_date = self.start_date

        for user in users:
            current_date = self.start_date

            while current_date <= self.end_date:
                month_start = current_date.replace(day=1)
                month_end = (
                    (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                )

                # Generate 20-40 transactions per user per month
                num_transactions = random.randint(20, 40)

                for _ in range(num_transactions):
                    # Random date within the month
                    tx_date = month_start + timedelta(
                        days=random.randint(0, (month_end - month_start).days)
                    )

                    # Select category
                    category = random.choice(list(TRANSACTION_CATEGORIES.keys()))
                    category_config = TRANSACTION_CATEGORIES[category]

                    # Generate amount
                    amount = round(
                        random.uniform(
                            category_config["min"], category_config["max"]
                        ),
                        2,
                    )

                    # Determine if recurring (some categories have monthly recurrence)
                    is_recurring = (
                        category_config["recurring"] == "monthly"
                        and random.random() > 0.3
                    )

                    # Select merchant
                    merchant = random.choice(
                        MERCHANTS.get(category, ["Unknown Merchant"])
                    )

                    transaction = {
                        "id": self.faker.uuid4(),
                        "user_id": user["id"],
                        "transaction_date": tx_date.date().isoformat(),
                        "amount": amount,
                        "category": category,
                        "description": f"{category} transaction",
                        "merchant_name": merchant,
                        "transaction_type": category_config["type"],
                        "payment_method": random.choice(
                            ["CASH", "CARD", "TRANSFER", "UPI", "CHEQUE"]
                        ),
                        "is_recurring": is_recurring,
                    }
                    transactions.append(transaction)

                # Move to next month
                current_date = (
                    (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                )
                current_date += timedelta(days=1)

        logger.info(f"Generated {len(transactions)} transactions")
        return transactions

    def generate_goals(self, users: List[dict]) -> List[dict]:
        """Generate financial goals (3-5 per user).

        Returns:
            List of goal dictionaries

        Example row:
            {
                'id': '550e8400-e29b-41d4-a716-446655440003',
                'user_id': '550e8400-e29b-41d4-a716-446655440000',
                'goal_name': 'Home Purchase',
                'description': 'Save for down payment',
                'target_amount': 500000.00,
                'current_amount': 125000.00,
                'target_date': '2026-12-31',
                'goal_type': 'HOME',
                'priority': 'HIGH',
                'status': 'ON_TRACK'
            }
        """
        goals = []

        for user in users:
            num_goals = random.randint(2, 5)

            for _ in range(num_goals):
                goal_type = random.choice(GOAL_TYPES)
                target_amount = round(
                    random.uniform(100000, 10000000), 2
                )  # Large target amounts
                current_amount = round(
                    random.uniform(0, target_amount), 2
                )  # Progress towards goal
                target_date = datetime.now() + timedelta(days=random.randint(30, 1825))

                goal = {
                    "id": self.faker.uuid4(),
                    "user_id": user["id"],
                    "goal_name": self._generate_goal_name(goal_type),
                    "description": f"Goal: {goal_type}",
                    "target_amount": target_amount,
                    "current_amount": current_amount,
                    "target_date": target_date.date().isoformat(),
                    "goal_type": goal_type,
                    "priority": random.choice(PRIORITIES),
                    "status": random.choice(
                        ["ACTIVE", "ON_TRACK", "AT_RISK", "COMPLETED"]
                    ),
                }
                goals.append(goal)

        logger.info(f"Generated {len(goals)} financial goals")
        return goals

    def generate_holdings(self, users: List[dict]) -> List[dict]:
        """Generate investment holdings (1-5 per user).

        Returns:
            List of holding dictionaries

        Example row:
            {
                'id': '550e8400-e29b-41d4-a716-446655440004',
                'user_id': '550e8400-e29b-41d4-a716-446655440000',
                'ticker': 'AAPL',
                'quantity': 50.00,
                'average_cost': 150.25,
                'current_value': 15050.00,
                'asset_type': 'EQUITY',
                'purchase_date': '2023-06-15',
                'last_updated': '2024-03-15'
            }
        """
        holdings = []

        for user in users:
            num_holdings = random.randint(1, 5)

            for _ in range(num_holdings):
                ticker = random.choice(AVAILABLE_TICKERS)
                quantity = round(random.uniform(1, 1000), 4)
                average_cost = round(random.uniform(50, 500), 2)
                current_value = round(quantity * random.uniform(50, 500), 2)
                asset_type = random.choice(ASSET_TYPES)
                purchase_date = self.start_date + timedelta(
                    days=random.randint(0, (self.end_date - self.start_date).days)
                )

                holding = {
                    "id": self.faker.uuid4(),
                    "user_id": user["id"],
                    "ticker": ticker,
                    "quantity": quantity,
                    "average_cost": average_cost,
                    "current_value": current_value,
                    "asset_type": asset_type,
                    "purchase_date": purchase_date.date().isoformat(),
                    "last_updated": self.end_date.date().isoformat(),
                }
                holdings.append(holding)

        logger.info(f"Generated {len(holdings)} investment holdings")
        return holdings

    def generate_market_prices(self) -> List[dict]:
        """Generate market price series for sample tickers using random walk.

        Returns:
            List of market_price dictionaries

        Example row:
            {
                'id': '550e8400-e29b-41d4-a716-446655440005',
                'ticker': 'AAPL',
                'price_date': '2024-03-15',
                'open_price': 149.50,
                'close_price': 151.25,
                'high_price': 152.00,
                'low_price': 149.00,
                'volume': 50000000
            }
        """
        prices = []

        for ticker in AVAILABLE_TICKERS:
            # Initial price
            current_price = round(random.uniform(50, 500), 2)
            date = self.start_date

            while date <= self.end_date:
                # Random walk: price change between -5% and +5% per day
                daily_change = np.random.normal(0, 0.02)  # Mean 0, std 2%
                new_price = current_price * (1 + daily_change)
                new_price = max(10, new_price)  # Floor at 10

                # OHLC values
                open_price = current_price
                close_price = round(new_price, 2)
                high_price = round(max(open_price, close_price) * 1.02, 2)
                low_price = round(min(open_price, close_price) * 0.98, 2)
                volume = random.randint(1000000, 100000000)

                price_record = {
                    "id": self.faker.uuid4(),
                    "ticker": ticker,
                    "price_date": date.date().isoformat(),
                    "open_price": round(open_price, 2),
                    "close_price": close_price,
                    "high_price": high_price,
                    "low_price": low_price,
                    "volume": volume,
                }
                prices.append(price_record)

                current_price = new_price
                date += timedelta(days=1)

        logger.info(f"Generated {len(prices)} market price records")
        return prices

    @staticmethod
    def _generate_goal_name(goal_type: str) -> str:
        """Generate realistic goal name based on type."""
        goal_names = {
            "SAVINGS": [
                "Emergency Fund",
                "Vacation Fund",
                "New Car",
                "House Renovation",
            ],
            "INVESTMENT": [
                "Stock Portfolio",
                "Mutual Fund Investment",
                "Dividend Portfolio",
            ],
            "DEBT_PAYOFF": [
                "Credit Card Payoff",
                "Student Loan Payoff",
                "Mortgage Payoff",
            ],
            "EDUCATION": [
                "Child's Education",
                "Master's Degree",
                "Professional Certification",
            ],
            "HOME": [
                "Home Purchase",
                "Down Payment",
                "Home Renovation",
            ],
            "RETIREMENT": [
                "Retirement Fund",
                "Pension Contribution",
                "Retirement Planning",
            ],
        }
        return random.choice(goal_names.get(goal_type, ["Financial Goal"]))

    def save_to_csv(self, output_dir: str = "data/") -> dict:
        """Generate all data and save to CSV files.

        Args:
            output_dir: Directory to save CSV files

        Returns:
            Dictionary with file paths and row counts
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate all data
        users = self.generate_users()
        financial_summaries = self.generate_financial_summary(users)
        transactions = self.generate_transactions(users)
        goals = self.generate_goals(users)
        holdings = self.generate_holdings(users)
        market_prices = self.generate_market_prices()

        # Save to CSV files
        files = {
            "users.csv": users,
            "financial_summary.csv": financial_summaries,
            "transactions.csv": transactions,
            "goals.csv": goals,
            "holdings.csv": holdings,
            "market_prices.csv": market_prices,
        }

        results = {}

        for filename, data in files.items():
            filepath = output_path / filename

            if not data:
                logger.warning(f"No data to write for {filename}")
                continue

            # Write CSV with DictWriter
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                fieldnames = list(data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            results[filename] = {
                "path": str(filepath),
                "rows": len(data),
                "columns": len(data[0]),
            }
            logger.info(f"Saved {len(data)} rows to {filepath}")

        return results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic financial data for testing"
    )
    parser.add_argument(
        "--n-users",
        type=int,
        default=100,
        help="Number of users to generate (default: 100)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=36,
        help="Number of months of history (default: 36)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--locale",
        type=str,
        default="en_US",
        help="Faker locale code (default: en_US)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="data/",
        help="Output directory for CSV files (default: data/)",
    )

    args = parser.parse_args()

    # Generate data
    generator = SyntheticDataGenerator(
        n_users=args.n_users,
        months=args.months,
        seed=args.seed,
        locale=args.locale,
    )

    results = generator.save_to_csv(output_dir=args.out_dir)

    # Print summary
    print("\n" + "=" * 70)
    print("SYNTHETIC DATA GENERATION COMPLETE")
    print("=" * 70)
    for filename, info in results.items():
        print(
            f"  {filename:30} {info['rows']:8} rows, {info['columns']:3} columns"
        )
    print("=" * 70)
    print(f"Output directory: {args.out_dir}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
