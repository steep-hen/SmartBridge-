#!/bin/bash
#
# Database migration runner script
#
# Usage:
#   ./scripts/migrate.sh                    # Run migrations (upgrade)
#   ./scripts/migrate.sh upgrade            # Upgrade to head
#   ./scripts/migrate.sh downgrade          # Downgrade
#   ./scripts/migrate.sh current            # Show current revision
#   ./scripts/migrate.sh history            # Show migration history
#
# Requires:
#   - DATABASE_URL environment variable set or defaults to config value
#   - Alembic installed (alembic)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Default command
COMMAND="${1:-upgrade}"

echo "Database Migration Runner"
echo "======================="
echo "Command: $COMMAND"
echo "Project Root: $PROJECT_ROOT"

# Validate Alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "ERROR: Alembic not found. Install with: pip install alembic"
    exit 1
fi

# Execute migration command
case "$COMMAND" in
    upgrade)
        echo "Running: alembic upgrade head"
        alembic upgrade head
        echo "✓ Migration completed successfully"
        ;;
    downgrade)
        echo "Running: alembic downgrade -1"
        alembic downgrade -1
        echo "✓ Downgrade completed successfully"
        ;;
    current)
        echo "Running: alembic current"
        alembic current
        ;;
    history)
        echo "Running: alembic history"
        alembic history
        ;;
    *)
        echo "ERROR: Unknown command: $COMMAND"
        echo ""
        echo "Available commands:"
        echo "  upgrade       - Upgrade to latest revision (default)"
        echo "  downgrade     - Downgrade one revision"
        echo "  current       - Show current revision"
        echo "  history       - Show migration history"
        exit 1
        ;;
esac
