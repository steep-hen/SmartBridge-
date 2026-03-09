"""AI layer for financial advice generation with safety and audit logging."""

from backend.ai.ai_client import AIClient, generate_advice
from backend.ai.prompt_templates import get_template, get_output_schema
from backend.ai.audit import get_audit_logger, AuditLogger

__all__ = [
    "AIClient",
    "generate_advice",
    "get_template",
    "get_output_schema",
    "get_audit_logger",
    "AuditLogger",
]
