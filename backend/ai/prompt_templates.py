"""Deterministic prompt templates for financial advice generation.

Three templates with varying risk profiles and explanation depth:
- conservative: Low-risk recommendations, minimal exposure
- balanced: Moderate recommendations, balanced risk-return
- explainability: Deep explanations with educational content

Each template enforces strict JSON output schema with no external text.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import json


@dataclass
class OutputSchema:
    """Strict output schema for model responses."""
    
    ADVICE_SCHEMA = {
        "type": "object",
        "required": ["actions", "instruments", "risk_warning", "assumptions", "sources"],
        "properties": {
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "priority", "rationale"],
                    "properties": {
                        "title": {"type": "string", "maxLength": 100},
                        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                        "rationale": {"type": "string", "maxLength": 500},
                    }
                },
                "minItems": 1,
                "maxItems": 10,
            },
            "instruments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type", "allocation_pct", "rationale"],
                    "properties": {
                        "name": {"type": "string", "maxLength": 100},
                        "type": {"type": "string", "enum": ["EQUITY", "BOND", "CASH", "COMMODITY", "ETF", "MUTUAL_FUND"]},
                        "allocation_pct": {"type": "number", "minimum": 0, "maximum": 100},
                        "rationale": {"type": "string", "maxLength": 300},
                    }
                },
                "maxItems": 15,
            },
            "risk_warning": {
                "type": "string",
                "minLength": 20,
                "maxLength": 500,
            },
            "assumptions": {
                "type": "object",
                "required": ["expected_annual_return", "inflation"],
                "properties": {
                    "expected_annual_return": {"type": "number", "minimum": -1, "maximum": 1},
                    "inflation": {"type": "number", "minimum": 0, "maximum": 1},
                }
            },
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "text_snippet"],
                    "properties": {
                        "id": {"type": "string", "maxLength": 100},
                        "text_snippet": {"type": "string", "maxLength": 200},
                    }
                },
                "maxItems": 10,
            },
        }
    }


class PromptTemplate:
    """Base prompt template with instruction enforcement."""
    
    COMMON_INSTRUCTIONS = """You MUST follow these rules:
1. Return ONLY valid JSON. Do not include any markdown, text, or explanations outside the JSON object.
2. Do not use the word "guarantee" or promise any specific returns.
3. Never state "X% return" or "100% safe" or any ROI promise.
4. Include a risk_warning that clearly states investments carry risk.
5. If citing sources, include them in the "sources" field with id and text_snippet.
6. Keep rationales concise (max 500 chars for actions, 300 for instruments).
7. Allocations should sum to reasonable levels (0-100%) but don't need to total 100%.
8. If uncertain, err on the side of caution and include disclaimers."""
    
    OUTPUT_SCHEMA_TEXT = json.dumps(OutputSchema.ADVICE_SCHEMA, indent=2)
    
    def __init__(self, name: str, profile: str, context: str):
        """Initialize template.
        
        Args:
            name: Template name (conservative, balanced, explainability)
            profile: Profile description for tone/risk level
            context: Context to inject into prompt
        """
        self.name = name
        self.profile = profile
        self.context = context
    
    def build_prompt(
        self,
        user_age: int,
        employment_status: str,
        risk_tolerance: str,
        savings_rate: float,
        debt_to_income: float,
        emergency_fund_months: float,
        investment_ratio: float,
        holdings: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        rag_references: List[str] = None,
    ) -> str:
        """Build prompt for model with user metrics.
        
        Args:
            user_age: User age
            employment_status: Employed, Self-employed, Retired, etc.
            risk_tolerance: Low, Medium, High
            savings_rate: % of income saved
            debt_to_income: Ratio
            emergency_fund_months: Months of coverage
            investment_ratio: % of net worth invested
            holdings: List of holdings dicts (ticker, type, allocation_pct)
            goals: List of goals (name, target, current, required_sip)
            rag_references: Optional list of reference snippets
            
        Returns:
            str: Formatted prompt ready for model
        """
        # Sanitize inputs to avoid prompt injection
        user_age = max(18, min(120, int(user_age)))
        employment_status = str(employment_status)[:50]
        risk_tolerance = str(risk_tolerance)[:20]
        
        # Build user profile summary
        profile_summary = f"""User Profile:
- Age: {user_age}
- Employment: {employment_status}
- Risk Tolerance: {risk_tolerance}

Financial Metrics:
- Savings Rate: {savings_rate:.2f}%
- Debt-to-Income Ratio: {debt_to_income:.4f}
- Emergency Fund Coverage: {emergency_fund_months:.2f} months
- Investment Ratio: {investment_ratio:.2%}

Current Holdings ({len(holdings)} items):
"""
        for holding in holdings[:10]:  # Limit to 10 for token management
            profile_summary += f"- {holding.get('name', 'Unknown')}: {holding.get('allocation_pct', 0):.1f}%\n"
        
        profile_summary += f"\nFinancial Goals ({len(goals)} items):\n"
        for goal in goals[:5]:  # Limit to 5 for token management
            profile_summary += f"- {goal.get('goal_name', 'Unknown')}: ${goal.get('current_amount', 0):.0f}/${goal.get('target_amount', 0):.0f} (needs ${goal.get('required_monthly_sip', 0):.2f}/month)\n"
        
        # Build references section
        references_text = ""
        if rag_references:
            references_text = "\n\nContext / References:\n"
            for i, ref in enumerate(rag_references[:3], 1):  # Top 3 refs
                references_text += f"{i}. {ref[:150]}...\n"
        
        prompt = f"""{self.profile}

{profile_summary}

{self.context}

{references_text}

CRITICAL INSTRUCTIONS:
{self.COMMON_INSTRUCTIONS}

REQUIRED OUTPUT SCHEMA (JSON):
```json
{self.OUTPUT_SCHEMA_TEXT}
```

Generate advice now. Return ONLY the JSON object, nothing else."""
        
        return prompt


class ConservativeTemplate(PromptTemplate):
    """Ultra-conservative template with minimal risk exposure."""
    
    def __init__(self):
        name = "conservative"
        profile = """You are a conservative financial advisor focused on capital preservation and downside protection.
Prioritize safety over returns. Recommend low-volatility assets and defensive strategies."""
        context = """Provide conservative financial advice using the metrics above. Focus on:
1. Building emergency reserves (target: 6+ months)
2. Low-cost index funds and bonds
3. Debt reduction strategies
4. Tax-efficient withdrawal plans
5. Defensive positioning in uncertain times

Assume moderate market returns (4-6% annually) and emphasize risk management."""
        super().__init__(name, profile, context)


class BalancedTemplate(PromptTemplate):
    """Balanced template with moderate risk-return tradeoff."""
    
    def __init__(self):
        name = "balanced"
        profile = """You are a balanced financial advisor focused on long-term wealth building with moderate risk.
Balance growth and safety. Recommend diversified portfolios aligned with risk tolerance."""
        context = """Provide balanced financial advice using the metrics above. Focus on:
1. Diversified asset allocation (60/40 or similar)
2. Long-term compounding through regular contributions
3. Risk-appropriate positioning for life stage
4. Goal-based investing strategy
5. Regular rebalancing and reoptimization

Assume market returns of 6-8% annually and explain risk-return tradeoff clearly."""
        super().__init__(name, profile, context)


class ExplainabilityTemplate(PromptTemplate):
    """Explainability-heavy template with educational focus."""
    
    def __init__(self):
        name = "explainability"
        profile = """You are an educational financial advisor focused on explaining concepts and building financial literacy.
Emphasize understanding over complexity. Teach principles while providing advice."""
        context = """Provide detailed, educational financial advice using the metrics above. Focus on:
1. Explaining WHY each recommendation makes sense (educational tone)
2. Teaching key financial concepts (compounding, diversification, risk)
3. Showing the math behind recommendations (e.g., FV calculations)
4. Providing learning resources and next steps
5. Empowering the user with knowledge to make informed decisions

Assume market returns of 5-7% annually. Include brief explanations of financial principles."""
        super().__init__(name, profile, context)


# Template registry
TEMPLATES = {
    "conservative": ConservativeTemplate(),
    "balanced": BalancedTemplate(),
    "explainability": ExplainabilityTemplate(),
}


def get_template(name: str) -> PromptTemplate:
    """Get template by name.
    
    Args:
        name: Template name (conservative, balanced, explainability)
        
    Returns:
        PromptTemplate instance
        
    Raises:
        ValueError: If template not found
    """
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template: {name}. Available: {list(TEMPLATES.keys())}")
    return TEMPLATES[name]


def get_output_schema() -> Dict[str, Any]:
    """Get strict output schema for validation.
    
    Returns:
        dict: JSON schema for response validation
    """
    return OutputSchema.ADVICE_SCHEMA.copy()
