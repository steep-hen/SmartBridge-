<# 
Database migration runner script (PowerShell)

Usage:
    .\scripts\migrate.ps1                    # Run migrations (upgrade)
    .\scripts\migrate.ps1 -Command upgrade   # Upgrade to head
    .\scripts\migrate.ps1 -Command downgrade # Downgrade
    .\scripts\migrate.ps1 -Command current   # Show current revision
    .\scripts\migrate.ps1 -Command history   # Show migration history

Requires:
    - DATABASE_URL environment variable set or defaults to config value
    - Alembic installed (python -m pip install alembic)
#>

param(
    [string]$Command = "upgrade"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Change to project root
Set-Location $ProjectRoot

Write-Host "Database Migration Runner" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host "Command: $Command"
Write-Host "Project Root: $ProjectRoot"
Write-Host ""

# Check if alembic is installed
try {
    $null = python -c "import alembic; print('ok')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Alembic not found"
    }
} catch {
    Write-Host "ERROR: Alembic not found. Install with: python -m pip install alembic" -ForegroundColor Red
    exit 1
}

# Execute migration command
switch ($Command.ToLower()) {
    "upgrade" {
        Write-Host "Running: alembic upgrade head" -ForegroundColor Yellow
        python -m alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Migration completed successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Migration failed" -ForegroundColor Red
            exit 1
        }
    }
    "downgrade" {
        Write-Host "Running: alembic downgrade -1" -ForegroundColor Yellow
        python -m alembic downgrade -1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Downgrade completed successfully" -ForegroundColor Green
        } else {
            Write-Host "✗ Downgrade failed" -ForegroundColor Red
            exit 1
        }
    }
    "current" {
        Write-Host "Running: alembic current" -ForegroundColor Yellow
        python -m alembic current
    }
    "history" {
        Write-Host "Running: alembic history" -ForegroundColor Yellow
        python -m alembic history
    }
    default {
        Write-Host "ERROR: Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Write-Host "Available commands:"
        Write-Host "  upgrade       - Upgrade to latest revision (default)"
        Write-Host "  downgrade     - Downgrade one revision"
        Write-Host "  current       - Show current revision"
        Write-Host "  history       - Show migration history"
        exit 1
    }
}
