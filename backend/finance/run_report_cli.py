"""CLI utility for generating and saving financial reports.

Usage:
    python backend/finance/run_report_cli.py --user-id <uuid> [--output-dir <dir>]
    
Output:
    Writes JSON report to outputs/reports/<user_id>.json
    Prints report to stdout (condensed format)
"""

import json
import sys
import argparse
from pathlib import Path
from uuid import UUID
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.models import Base
from backend.finance.report_builder import build_user_report


def ensure_output_directory(output_dir: Path) -> Path:
    """Create output directory if it doesn't exist."""
    output_dir = output_dir / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generate_and_save_report(
    user_id: str,
    output_dir: Path = None,
) -> dict:
    """Generate financial report for user and save to JSON.
    
    Args:
        user_id: UUID string of user
        output_dir: Output directory (default: outputs/reports/)
        
    Returns:
        dict: Generated report
        
    Raises:
        ValueError: If user UUID is invalid or user not found
        SQLAlchemy errors: If database connection fails
    """
    # Parse and validate UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError as e:
        raise ValueError(f"Invalid UUID format: {user_id}") from e
    
    # Default output directory
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "outputs"
    
    output_dir = ensure_output_directory(output_dir)
    
    # Connect to database
    engine = create_engine(settings.db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Generate report
        print(f"Generating report for user {user_uuid}...", file=sys.stderr)
        report = build_user_report(user_uuid, db)
        
        # Save to JSON
        output_file = output_dir / f"{user_uuid}.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report saved to {output_file}", file=sys.stderr)
        return report
        
    finally:
        db.close()


def print_report_summary(report: dict) -> None:
    """Print condensed report summary to stdout.
    
    Args:
        report: Generated financial report dict
    """
    user = report['user_profile']
    metrics = report['computed_metrics']
    health = report['overall_health_score']
    
    print("\n" + "="*70)
    print(f"FINANCIAL REPORT: {user['name']} ({user['email']})")
    print("="*70)
    
    print(f"\nHealth Score: {health}/100")
    print(f"Savings Rate: {metrics['savings_rate']:.2f}%")
    print(f"Debt-to-Income: {metrics['debt_to_income_ratio']*100:.2f}%")
    print(f"Emergency Fund: {metrics['emergency_fund_months']:.1f} months")
    print(f"Investment Ratio: {metrics['investment_ratio']*100:.2f}%")
    
    snapshot = report['financial_snapshot']
    if snapshot['available']:
        print(f"\nFinancial Snapshot ({snapshot['period']}):")
        print(f"  Monthly Income: ${metrics['monthly_income']:,.2f}")
        print(f"  Monthly Expenses: ${metrics['monthly_expenses']:,.2f}")
        print(f"  Net Worth: ${snapshot['net_worth']:,.2f}")
    
    holdings = report['holdings_summary']
    if holdings['count'] > 0:
        print(f"\nPortfolio ({holdings['count']} positions):")
        print(f"  Total Value: ${holdings['total_current_value']:,.2f}")
        print(f"  Unrealized Gain/Loss: ${holdings['total_unrealized_gain_loss']:,.2f} ({holdings['gain_loss_percentage']:.2f}%)")
    
    goals = report['goals_analysis']
    if goals['count'] > 0:
        summary = goals['achievement_summary']
        print(f"\nGoals ({goals['count']} total):")
        print(f"  Achievable: {summary['achievable_count']}/{summary['total_goals']}")
        print(f"  Avg Progress: {summary['total_progress_percentage']:.1f}%")
    
    print("\n" + "="*70 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate and save financial reports for users.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/finance/run_report_cli.py --user-id 550e8400-e29b-41d4-a716-446655440000
  python backend/finance/run_report_cli.py --user-id 550e8400-e29b-41d4-a716-446655440000 --output-dir ./reports
        """,
    )
    
    parser.add_argument(
        '--user-id',
        type=str,
        required=True,
        help='UUID of user to generate report for',
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory (default: outputs/reports/)',
    )
    
    args = parser.parse_args()
    
    try:
        # Generate report
        report = generate_and_save_report(
            user_id=args.user_id,
            output_dir=args.output_dir,
        )
        
        # Print summary
        print_report_summary(report)
        
        # Return success
        return 0
        
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
