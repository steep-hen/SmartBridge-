"""Provider-agnostic AI client for financial advice generation.

Supports Gemini API with fallback to deterministic local mode.
Includes JSON schema validation, content filtering, and audit logging.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from functools import lru_cache
import time

import jsonschema

from backend.ai.prompt_templates import get_template, get_output_schema
from backend.ai.audit import get_audit_logger, AuditLogger


logger = logging.getLogger(__name__)


class AIClient:
    """Provider-agnostic AI client with Gemini + fallback support."""
    
    # Cache config
    CACHE_TTL_SECONDS = 300  # 5 minutes
    
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        """Initialize AI client.
        
        Args:
            api_key: Gemini API key (optional, reads from GEMINI_API_KEY env var if not provided)
            endpoint: Gemini API endpoint (defaults to official)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.endpoint = endpoint or os.getenv("GEMINI_API_ENDPOINT", "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent")
        self.audit_logger = get_audit_logger()
        self.schema = get_output_schema()
        
        # Simple in-memory cache: (prompt_hash) -> (response, timestamp)
        self._cache = {}
        
        self.has_gemini = bool(self.api_key)
        logger.info(f"AI Client initialized. Gemini available: {self.has_gemini}")
    
    def _get_cached_response(self, prompt_hash: str) -> Optional[str]:
        """Get cached response if not expired.
        
        Args:
            prompt_hash: Hash of prompt
            
        Returns:
            Cached response or None if not cached/expired
        """
        if prompt_hash in self._cache:
            response, timestamp = self._cache[prompt_hash]
            if time.time() - timestamp < self.CACHE_TTL_SECONDS:
                logger.info(f"Cache hit for prompt {prompt_hash}")
                return response
            else:
                del self._cache[prompt_hash]
        return None
    
    def _set_cache(self, prompt_hash: str, response: str) -> None:
        """Cache response.
        
        Args:
            prompt_hash: Hash of prompt
            response: Response to cache
        """
        self._cache[prompt_hash] = (response, time.time())
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API safely.
        
        Args:
            prompt: Prompt text
            
        Returns:
            str: Model response
            
        Raises:
            Exception: If API call fails
        """
        try:
            import google.generativeai as genai
        except ImportError:
            logger.warning("google-generativeai not installed, using fallback")
            return self._generate_local_fallback_advice(prompt)
        
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-pro")
            
            # Set timeout and token limit
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,  # Reasonable limit for JSON
                ),
                request_options={
                    "timeout": 30,  # 30 second timeout
                }
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}. Using fallback.")
            return self._generate_local_fallback_advice(prompt)
    
    def _generate_local_fallback_advice(self, prompt: str) -> str:
        """Generate deterministic local fallback advice.
        
        Args:
            prompt: Prompt (used to extract metrics)
            
        Returns:
            str: JSON response matching schema
        """
        # Extract metrics from prompt (heuristic parsing)
        # In real use, we'd have structured data, but for now we create safe defaults
        
        fallback_response = {
            "actions": [
                {
                    "title": "Build Emergency Fund to 6 Months",
                    "priority": 1,
                    "rationale": "Establish financial resilience before aggressive investing. Target 6 months of living expenses in accessible savings."
                },
                {
                    "title": "Review Asset Allocation",
                    "priority": 2,
                    "rationale": "Ensure diversification across asset classes appropriate for your risk tolerance and time horizon."
                },
                {
                    "title": "Automate Savings and Investment",
                    "priority": 3,
                    "rationale": "Set up automatic transfers to invest regularly (dollar-cost averaging) and reduce behavioral biases."
                },
            ],
            "instruments": [
                {
                    "name": "Low-Cost Total Market Index Fund (e.g., VTI, VTSAX)",
                    "type": "ETF",
                    "allocation_pct": 40.0,
                    "rationale": "Provides broad equity exposure with minimal fees. Core holding for most portfolios."
                },
                {
                    "name": "Bond Index Fund (e.g., BND, VBTLX)",
                    "type": "BOND",
                    "allocation_pct": 30.0,
                    "rationale": "Reduces volatility and provides downside protection. Appropriate for diversification."
                },
                {
                    "name": "High-Yield Savings or Money Market",
                    "type": "CASH",
                    "allocation_pct": 30.0,
                    "rationale": "Liquid reserves for emergency fund and near-term goals. Focus on FDIC-insured accounts."
                },
            ],
            "risk_warning": "All investments carry risk, including potential loss of principal. Past performance does not guarantee future results. Consider consulting a financial advisor before making investment decisions. This advice is educational and not personalized financial guidance.",
            "assumptions": {
                "expected_annual_return": 0.06,  # Conservative 6%
                "inflation": 0.03,  # 3% inflation assumption
            },
            "sources": [
                {
                    "id": "bogle_2003",
                    "text_snippet": "Low-cost, diversified index funds are the most reliable path to long-term wealth building for most investors."
                },
                {
                    "id": "markowitz_1952",
                    "text_snippet": "Portfolio diversification reduces risk by spreading investments across uncorrelated assets."
                },
            ],
        }
        
        return json.dumps(fallback_response)
    
    def _validate_response_schema(self, response_json: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Validate response against schema.
        
        Args:
            response_json: JSON response from model
            
        Returns:
            tuple: (parsed_dict or None, error_message or None)
        """
        try:
            parsed = json.loads(response_json)
            # Validate against schema
            jsonschema.validate(instance=parsed, schema=self.schema)
            return parsed, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON: {str(e)}"
        except jsonschema.ValidationError as e:
            return None, f"Schema validation failed: {e.message}"
    
    def _apply_content_filters(self, response_dict: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Check response for forbidden content.
        
        Args:
            response_dict: Parsed response dict
            
        Returns:
            tuple: (is_blocked, reason_if_blocked)
        """
        # Stringify entire response to check all fields
        response_str = json.dumps(response_dict).lower()
        
        # Refined check: allow "does not guarantee" disclaimers
        # but block standalone "guarantee" promises
        forbidden = AuditLogger.check_forbidden_phrases(response_str)
        if forbidden:
            # Allow if it's a disclaimer like "does not guarantee" or "not guaranteed"
            if "does not guarantee" not in response_str and "not guaranteed" not in response_str and "no guarantee" not in response_str:
                return True, f"Contains forbidden phrase: '{forbidden}'"
        
        # Additional checks: ensure no promise of specific returns
        if "%" in response_str and "return" in response_str:
            # Parse out suspicious patterns like "10% return" or "will return"
            for part in response_str.split():
                if "%" in part:
                    # Check context - is it a promise?
                    idx = response_str.find(part)
                    context = response_str[max(0, idx-30):min(len(response_str), idx+30)]
                    if any(word in context for word in ["will", "should", "promise", "certain"]) and "not" not in context:
                        return True, f"Suspicious return promise detected in context: ...{context}..."
        
        return False, None
    
    def generate_advice(
        self,
        report: Dict[str, Any],
        template: str = "balanced",
    ) -> Dict[str, Any]:
        """Generate financial advice from report.
        
        Args:
            report: Financial report dict (from build_user_report)
            template: Template name (conservative, balanced, explainability)
            
        Returns:
            dict: Advice response (validated JSON)
            
        Raises:
            ValueError: If response is invalid and cannot be fallback
        """
        # Extract user ID and model version
        user_id = report.get("user_profile", {}).get("user_id", "unknown")
        prompt_template = get_template(template)
        
        # Extract metrics from report (with safety)
        user_profile = report.get("user_profile", {})
        metrics = report.get("computed_metrics", {})
        holdings = report.get("holdings_summary", {}).get("holdings", [])
        goals = report.get("goals_analysis", {}).get("goals", [])
        
        # Extract user metadata
        user_age = int(user_profile.get("age", 35))  # Default to 35
        employment_status = str(user_profile.get("employment_status", "Employed"))
        risk_tolerance = str(user_profile.get("risk_tolerance", "Medium"))
        
        # RAG-lite references (mock for now - in production would query market data DB)
        rag_references = [
            "Index funds typically have lower fees than actively managed funds, improving long-term returns.",
            "Asset allocation (stocks/bonds/cash) is more important than individual security selection.",
            "Dollar-cost averaging reduces timing risk when investing.",
        ]
        
        # Build prompt
        prompt = prompt_template.build_prompt(
            user_age=user_age,
            employment_status=employment_status,
            risk_tolerance=risk_tolerance,
            savings_rate=metrics.get("savings_rate", 0.0),
            debt_to_income=metrics.get("debt_to_income_ratio", 0.0),
            emergency_fund_months=metrics.get("emergency_fund_months", 0.0),
            investment_ratio=metrics.get("investment_ratio", 0.0),
            holdings=holdings,
            goals=goals,
            rag_references=rag_references,
        )
        
        # Check cache
        prompt_hash = AuditLogger.hash_text(prompt)
        cached = self._get_cached_response(prompt_hash)
        if cached:
            response_json = cached
            model_used = "cache"
            model_version = "cached"
        else:
            # Call model (Gemini or fallback)
            if self.has_gemini:
                try:
                    response_json = self._call_gemini(prompt)
                    model_used = "gemini"
                    model_version = "gemini-pro"
                except Exception as e:
                    logger.error(f"Gemini failed: {e}, using fallback")
                    response_json = self._generate_local_fallback_advice(prompt)
                    model_used = "local-fallback"
                    model_version = "fallback-v1"
            else:
                response_json = self._generate_local_fallback_advice(prompt)
                model_used = "local-fallback"
                model_version = "fallback-v1"
            
            # Cache result
            self._set_cache(prompt_hash, response_json)
        
        # Validate schema
        validated_response, validation_error = self._validate_response_schema(response_json)
        
        if validation_error:
            logger.error(f"Schema validation failed: {validation_error}. Using fallback.")
            response_json = self._generate_local_fallback_advice(prompt)
            validated_response, validation_error = self._validate_response_schema(response_json)
            model_used = "local-fallback"
            model_version = "fallback-v1"
            
            if validation_error:
                # Last resort: return safe fallback dict
                validated_response = json.loads(
                    self._generate_local_fallback_advice(prompt)
                )
                validation_error = f"Fallback used: {validation_error}"
        
        # Apply content filters
        blocked, blocked_reason = self._apply_content_filters(validated_response)
        
        if blocked:
            logger.warning(f"Content blocked for user {user_id}: {blocked_reason}")
            # Replace with safe risk warning and reset to fallback
            fallback_dict = json.loads(
                self._generate_local_fallback_advice(prompt)
            )
            validated_response = fallback_dict
            blocked = True
        
        # Log audit entry
        self.audit_logger.log_call(
            user_id=user_id,
            model_used=model_used,
            model_version=model_version,
            template_used=template,
            input_report=report,
            prompt=prompt,
            raw_model_response=response_json,
            validated_response=validated_response if not blocked else None,
            validation_errors=validation_error,
        )
        
        # If blocked, return safe version with risk warning
        if blocked:
            logger.warning(f"Returning safe fallback due to content filter.")
            return validated_response
        
        return validated_response


def generate_advice(
    report: Dict[str, Any],
    template: str = "balanced",
) -> Dict[str, Any]:
    """Convenience function to generate advice.
    
    Args:
        report: Financial report dict
        template: Template name
        
    Returns:
        dict: Advice response
    """
    client = AIClient()
    return client.generate_advice(report, template=template)
