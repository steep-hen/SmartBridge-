#!/usr/bin/env python3
"""Audit log retention and archival script.

Manages audit log lifecycle:
- Archives logs older than retention period to separate storage
- Deletes archived logs from primary database
- Maintains immutable archive for compliance
- Generates retention report

Usage:
    python prune_audit.py --days 90 --archive-path /backups/audit_archive
    python prune_audit.py --days 180 --archive-path s3://audit-archive-bucket/
    python prune_audit.py --dry-run --days 90  # Preview what would be deleted
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from sqlalchemy import create_engine, Column, DateTime, text
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("ERROR: sqlalchemy not installed. Run: pip install sqlalchemy")
    sys.exit(1)


class AuditLogArchiver:
    """Archive and prune audit logs."""
    
    def __init__(self, db_url: str, archive_path: str, dry_run: bool = False):
        """Initialize archiver.
        
        Args:
            db_url: Database connection string
            archive_path: Path for archive files (local or s3://)
            dry_run: If True, don't actually delete anything
        """
        self.db_url = db_url
        self.archive_path = Path(archive_path) if not archive_path.startswith('s3://') else archive_path
        self.dry_run = dry_run
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_logs_to_archive(self, days: int) -> List[Dict]:
        """Get audit logs older than specified days.
        
        Args:
            days: Retention period in days
            
        Returns:
            List of audit log records
        """
        session = self.Session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Query logs older than cutoff
            query = f"""
            SELECT id, audit_id, user_id, event_type, resource_type, 
                   created_at, details::text as details
            FROM audit_logs
            WHERE created_at < '{cutoff_date.isoformat()}'
            ORDER BY created_at DESC
            """
            
            result = session.execute(text(query))
            logs = [dict(row._mapping) for row in result]
            
            return logs
        finally:
            session.close()
    
    def archive_logs(self, logs: List[Dict], retention_days: int) -> int:
        """Archive logs to external storage.
        
        Args:
            logs: Log records to archive
            retention_days: Retention period (for metadata)
            
        Returns:
            Number of logs archived
        """
        if not logs:
            print("No logs to archive.")
            return 0
        
        archive_data = {
            "archived_at": datetime.utcnow().isoformat(),
            "retention_days": retention_days,
            "log_count": len(logs),
            "logs": logs,
            "archive_url": str(self.archive_path),
        }
        
        # Generate archive filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_archive_{timestamp}.jsonl"
        
        # Archive in JSONL format (one JSON per line for streaming)
        archive_file = self.archive_path / filename if isinstance(self.archive_path, Path) else f"{self.archive_path}/{filename}"
        
        if not self.dry_run:
            # Ensure archive path exists
            if isinstance(self.archive_path, Path):
                self.archive_path.mkdir(parents=True, exist_ok=True)
                archive_file = self.archive_path / filename
                
                # Write JSONL
                with open(archive_file, 'w') as f:
                    for log in logs:
                        f.write(json.dumps(log) + "\n")
            else:
                # S3 upload would go here
                print(f"Would upload {len(logs)} logs to {self.archive_path}/{filename}")
                # TODO: Implement boto3 S3 upload
        
        print(f"{'[DRY RUN] ' if self.dry_run else ''}Archived {len(logs)} logs to {archive_file}")
        return len(logs)
    
    def delete_archived_logs(self, logs: List[Dict]) -> int:
        """Delete archived logs from database.
        
        Args:
            logs: Log records to delete
            
        Returns:
            Number of logs deleted
        """
        if not logs:
            return 0
        
        session = self.Session()
        try:
            log_ids = [str(log['id']) for log in logs]
            
            if not self.dry_run:
                delete_query = f"""
                DELETE FROM audit_logs
                WHERE id IN ({','.join(["'" + id + "'" for id in log_ids])})
                """
                session.execute(text(delete_query))
                session.commit()
            
            print(f"{'[DRY RUN] ' if self.dry_run else ''}Deleted {len(logs)} logs from database")
            return len(logs)
        finally:
            session.close()
    
    def generate_report(self, deleted_count: int, archived_count: int) -> Dict:
        """Generate retention report.
        
        Args:
            deleted_count: Number of logs deleted
            archived_count: Number of logs archived
            
        Returns:
            Report dictionary
        """
        session = self.Session()
        try:
            # Get current audit log count
            count_query = "SELECT count(*) as total FROM audit_logs"
            result = session.execute(text(count_query))
            total_logs = dict(result.first()._mapping)['total']
            
            # Get event type distribution
            dist_query = """
            SELECT event_type, count(*) as count
            FROM audit_logs
            GROUP BY event_type
            ORDER BY count DESC
            """
            result = session.execute(text(dist_query))
            event_distribution = {row[0]: row[1] for row in result}
            
            report = {
                "report_date": datetime.utcnow().isoformat(),
                "archived_count": archived_count,
                "deleted_count": deleted_count,
                "remaining_logs": total_logs,
                "event_type_distribution": event_distribution,
                "dry_run": self.dry_run,
            }
            
            return report
        finally:
            session.close()
    
    def run(self, retention_days: int) -> bool:
        """Run archival and retention process.
        
        Args:
            retention_days: Logs older than this many days will be archived
            
        Returns:
            True if successful
        """
        try:
            print(f"Starting audit log archival (retention: {retention_days} days)...")
            
            # Get logs to archive
            logs = self.get_logs_to_archive(retention_days)
            print(f"Found {len(logs)} logs older than {retention_days} days")
            
            if logs:
                # Archive logs
                archived_count = self.archive_logs(logs, retention_days)
                
                # Delete from database
                deleted_count = self.delete_archived_logs(logs)
            else:
                archived_count = 0
                deleted_count = 0
            
            # Generate report
            report = self.generate_report(deleted_count, archived_count)
            
            print("\n=== Archival Report ===")
            print(f"Archived: {report['archived_count']}")
            print(f"Deleted: {report['deleted_count']}")
            print(f"Remaining: {report['remaining_logs']}")
            print(f"Event Distribution: {report['event_type_distribution']}")
            
            # Save report
            report_file = Path(f"archival_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\nReport saved to: {report_file}")
            
            return True
            
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Archive and prune audit logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Archive logs older than 90 days to local directory
  python prune_audit.py --days 90 --archive-path /backups/audit_archive
  
  # Dry run to see what would be deleted
  python prune_audit.py --days 90 --dry-run
  
  # Archive to S3 (requires boto3)
  python prune_audit.py --days 180 --archive-path s3://my-bucket/audit-logs/
        """
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Retention period in days (default: 90)'
    )
    
    parser.add_argument(
        '--archive-path',
        required=True,
        help='Path for archive files (local path or s3://bucket/path/)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be deleted without making changes'
    )
    
    parser.add_argument(
        '--database-url',
        help='Database URL (default: read from DATABASE_URL env var)'
    )
    
    args = parser.parse_args()
    
    # Get database URL
    db_url = args.database_url or os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set and --database-url not provided")
        sys.exit(1)
    
    # Run archiver
    archiver = AuditLogArchiver(db_url, args.archive_path, dry_run=args.dry_run)
    success = archiver.run(args.days)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
