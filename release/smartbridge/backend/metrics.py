"""Prometheus metrics instrumentation for SmartBridge backend.

Exposes metrics for:
- HTTP request latency and counts
- AI model calls and failures
- Database operations
- Audit log operations

Usage:
    from backend.metrics import track_request, track_ai_call
    
    @app.middleware("http")
    async def metrics_middleware(request, call_next):
        track_request(request)
        response = await call_next(request)
        track_request(request, response.status_code)
        return response
"""

from prometheus_client import Counter, Histogram, Gauge, expose_metrics
from typing import Optional, List
import time

# ============================================================================
# REQUEST METRICS
# ============================================================================

request_count = Counter(
    'request_count_total',
    'Total HTTP requests',
    ['method', 'path', 'status']
)

request_latency = Histogram(
    'request_latency_seconds',
    'HTTP request latency in seconds',
    ['method', 'path'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# ============================================================================
# AI METRICS
# ============================================================================

ai_calls = Counter(
    'ai_calls_total',
    'Total AI API calls',
    ['model_used', 'status', 'template']
)

ai_latency = Histogram(
    'ai_latency_seconds',
    'AI API call latency in seconds',
    ['model_used'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

ai_failures = Counter(
    'ai_failures_total',
    'Total AI API failures',
    ['model_used', 'error_type']
)

# ============================================================================
# DATABASE METRICS
# ============================================================================

db_operations = Counter(
    'db_operations_total',
    'Total database operations',
    ['operation', 'table', 'status']
)

db_latency = Histogram(
    'db_latency_seconds',
    'Database operation latency',
    ['operation'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# ============================================================================
# AUDIT & CONSENT METRICS
# ============================================================================

audit_entries = Counter(
    'audit_entries_total',
    'Total audit log entries created',
    ['event_type', 'resource_type']
)

consent_records = Counter(
    'consent_records_total',
    'Total consent records created',
    ['scope', 'status']
)

# ============================================================================
# BUSINESS METRICS
# ============================================================================

active_users = Gauge(
    'active_users_current',
    'Current number of active users'
)

reports_generated = Counter(
    'reports_generated_total',
    'Total financial reports generated',
    ['status']
)

advice_generated = Counter(
    'advice_generated_total',
    'Total AI advice generated',
    ['template', 'status']
)

# ============================================================================
# TRACKING FUNCTIONS
# ============================================================================

def track_request(method: str, path: str, status_code: int, latency: float):
    """Track HTTP request metrics.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: Response status code
        latency: Request latency in seconds
    """
    # Normalize path to avoid cardinality explosion
    normalized_path = _normalize_path(path)
    
    request_count.labels(method=method, path=normalized_path, status=status_code).inc()
    request_latency.labels(method=method, path=normalized_path).observe(latency)


def track_ai_call(
    model_used: str,
    status: str,
    template: str = 'balanced',
    latency: Optional[float] = None,
    error_type: Optional[str] = None,
):
    """Track AI API call metrics.
    
    Args:
        model_used: Model name (e.g., 'gemini', 'fallback')
        status: Call status ('success', 'failure', 'fallback')
        template: Advice template ('balanced', 'conservative', 'explainability')
        latency: Call latency in seconds
        error_type: Error type if failed (e.g., 'rate_limit', 'auth_error')
    """
    ai_calls.labels(
        model_used=model_used,
        status=status,
        template=template
    ).inc()
    
    if latency is not None:
        ai_latency.labels(model_used=model_used).observe(latency)
    
    if error_type is not None:
        ai_failures.labels(
            model_used=model_used,
            error_type=error_type
        ).inc()


def track_db_operation(
    operation: str,
    table: str,
    status: str = 'success',
    latency: Optional[float] = None,
):
    """Track database operation metrics.
    
    Args:
        operation: Operation type ('select', 'insert', 'update', 'delete')
        table: Table name
        status: Operation status ('success', 'failure')
        latency: Operation latency in seconds
    """
    db_operations.labels(
        operation=operation,
        table=table,
        status=status
    ).inc()
    
    if latency is not None:
        db_latency.labels(operation=operation).observe(latency)


def track_audit_event(event_type: str, resource_type: str):
    """Track audit log event.
    
    Args:
        event_type: Type of audit event ('create', 'read', 'update', 'delete')
        resource_type: Type of resource being audited ('user', 'report', 'advice')
    """
    audit_entries.labels(
        event_type=event_type,
        resource_type=resource_type
    ).inc()


def track_consent(scope: str, status: str = 'recorded'):
    """Track consent record.
    
    Args:
        scope: Consent scope ('data_analysis', 'ai_advice', 'data_export')
        status: Consent status ('recorded', 'withdrawn')
    """
    consent_records.labels(scope=scope, status=status).inc()


def track_report_generation(status: str = 'success'):
    """Track financial report generation.
    
    Args:
        status: Generation status ('success', 'failure')
    """
    reports_generated.labels(status=status).inc()


def track_advice_generation(template: str, status: str = 'success'):
    """Track AI advice generation.
    
    Args:
        template: Advice template used
        status: Generation status ('success', 'failure', 'fallback')
    """
    advice_generated.labels(template=template, status=status).inc()


def set_active_users_count(count: int):
    """Set gauge for active users.
    
    Args:
        count: Number of active users
    """
    active_users.set(count)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _normalize_path(path: str) -> str:
    """Normalize path to avoid cardinality explosion.
    
    Converts /reports/123e4567-... to /reports/{id}
    
    Args:
        path: Original request path
        
    Returns:
        Normalized path
    """
    import re
    
    # Replace UUIDs with {id}
    normalized = re.sub(
        r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        '{id}',
        path,
        flags=re.IGNORECASE
    )
    
    # Replace numeric IDs with {id}
    normalized = re.sub(r'/\d+([/?]|$)', r'/{id}\1', normalized)
    
    return normalized


def get_metrics_exposition() -> str:
    """Get Prometheus metrics in exposition format.
    
    Returns:
        Metrics in text format suitable for Prometheus scraping
    """
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return generate_latest().decode('utf-8')
