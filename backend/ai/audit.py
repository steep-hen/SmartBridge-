"""Immutable audit logging system for compliance and security.

Records all AI model calls with input/output validation, content filtering results,
and model identification for complete traceability.
"""

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4
from dataclasses import dataclass, asdict
import os


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    
    audit_id: str  # Unique ID for this entry
    timestamp: str  # ISO format
    user_id: str  # User being analyzed
    model_used: str  # "gemini" or "local-fallback"
    model_version: str  # e.g., "gemini-pro", "fallback-v1"
    template_used: str  # Template name
    input_report_hash: str  # Hash of input report for traceability
    prompt_hash: str  # Hash of prompt to detect duplicates
    raw_model_response: str  # Full model output (before validation)
    validated_response: Optional[str]  # Parsed/validated output (JSON string)
    blocked_flag: bool  # Whether output was blocked by content filter
    reason_if_blocked: Optional[str]  # Why it was blocked
    validation_errors: Optional[str]  # JSON validation errors if any
    
    def to_ndjson_line(self) -> str:
        """Serialize to NDJSON format."""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        """Create from dict."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class AuditLogger:
    """Writes immutable audit logs to file and database."""
    
    # Forbidden phrases that trigger content blocking
    FORBIDDEN_PHRASES = [
        "guarantee",
        "guaranteed",
        "100% return",
        "guaranteed return",
        "promised return",
        "risk-free",
        "no risk",
        "certain return",
        "sure profit",
        "will definitely",
        "absolutely safe",
        "never lose",
    ]
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize audit logger.
        
        Args:
            log_dir: Directory to write audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "audit_log.ndjson"
        
        # Set up Python logger for info messages
        self.logger = logging.getLogger("audit")
        handler = logging.FileHandler(self.log_dir / "audit_info.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @staticmethod
    def hash_text(text: str) -> str:
        """Hash text for deduplication."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    @staticmethod
    def check_forbidden_phrases(text: str) -> Optional[str]:
        """Check if text contains forbidden phrases.
        
        Args:
            text: Text to check
            
        Returns:
            Forbidden phrase found, or None
        """
        text_lower = text.lower()
        for phrase in AuditLogger.FORBIDDEN_PHRASES:
            if phrase in text_lower:
                return phrase
        return None
    
    def log_call(
        self,
        user_id: str,
        model_used: str,
        model_version: str,
        template_used: str,
        input_report: Dict[str, Any],
        prompt: str,
        raw_model_response: str,
        validated_response: Optional[Dict[str, Any]] = None,
        validation_errors: Optional[str] = None,
    ) -> AuditEntry:
        """Log a complete AI model call.
        
        Args:
            user_id: User ID
            model_used: "gemini" or "local-fallback"
            model_version: Model version string
            template_used: Template name used
            input_report: Input report dict
            prompt: Prompt sent to model
            raw_model_response: Raw model output
            validated_response: Parsed/validated response (if successful)
            validation_errors: Validation errors if any
            
        Returns:
            AuditEntry: The logged entry
        """
        # Check for content filtering violations
        blocked_flag = False
        reason_if_blocked = None
        
        forbidden = self.check_forbidden_phrases(raw_model_response)
        if forbidden:
            # Allow if it's a safe disclaimer like "does not guarantee" or "not guaranteed"
            if ("does not guarantee" not in raw_model_response.lower() and 
                "not guaranteed" not in raw_model_response.lower() and 
                "no guarantee" not in raw_model_response.lower()):
                blocked_flag = True
                reason_if_blocked = f"Contains forbidden phrase: '{forbidden}'"
        
        # Create audit entry
        entry = AuditEntry(
            audit_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=user_id,
            model_used=model_used,
            model_version=model_version,
            template_used=template_used,
            input_report_hash=self.hash_text(json.dumps(input_report, sort_keys=True)),
            prompt_hash=self.hash_text(prompt),
            raw_model_response=raw_model_response,
            validated_response=json.dumps(validated_response) if validated_response else None,
            blocked_flag=blocked_flag,
            reason_if_blocked=reason_if_blocked,
            validation_errors=validation_errors,
        )
        
        # Write to NDJSON file (immutable append)
        with open(self.log_file, "a") as f:
            f.write(entry.to_ndjson_line() + "\n")
        
        # Log info message
        if blocked_flag:
            self.logger.warning(
                f"Content blocked for user {user_id}: {reason_if_blocked}"
            )
        else:
            self.logger.info(
                f"Model call logged for user {user_id} using {model_used}/{template_used}"
            )
        
        return entry
    
    def read_audit_log(self, limit: int = 0) -> list:
        """Read audit log entries.
        
        Args:
            limit: Max entries to read (0 = all)
            
        Returns:
            list: List of AuditEntry dicts
        """
        if not self.log_file.exists():
            return []
        
        entries = []
        with open(self.log_file, "r") as f:
            for i, line in enumerate(f):
                if limit > 0 and i >= limit:
                    break
                try:
                    data = json.loads(line.strip())
                    entries.append(data)
                except json.JSONDecodeError:
                    continue
        
        return entries
    
    def get_user_audit_trail(self, user_id: str) -> list:
        """Get all audit entries for a user.
        
        Args:
            user_id: User ID to filter by
            
        Returns:
            list: Matching AuditEntry dicts
        """
        all_entries = self.read_audit_log()
        return [e for e in all_entries if e.get("user_id") == user_id]
    
    def get_blocked_entries(self) -> list:
        """Get all blocked/flagged entries.
        
        Returns:
            list: Entries with blocked_flag=true
        """
        all_entries = self.read_audit_log()
        return [e for e in all_entries if e.get("blocked_flag")]


# Global audit logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger.
    
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
