"""Contextual Prompt Builder - generates Gemini prompts from full financial context.

Integrates all financial data (profile, metrics, spending, goals, portfolio)
into a single comprehensive prompt for AI-powered financial advice.

Output structure:
{
  "budget_advice": [{"title": str, "action": str, "rationale": str}, ...],
  "debt_strategy": [{"title": str, "action": str, "rationale": str}, ...],
  "investment_strategy": [{"title": str, "action": str, "rationale": str}, ...],
  "goal_roadmap": [{"title": str, "action": str, "rationale": str}, ...],
  "risk_explanation": str,
  "human_summary": str
}
"""

import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
import jsonschema


# ============================================================================
# OUTPUT SCHEMA VALIDATION
# ============================================================================

CONTEXTUAL_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "budget_advice",
        "debt_strategy",
        "investment_strategy",
        "goal_roadmap",
        "risk_explanation",
        "human_summary"
    ],
    "properties": {
        "budget_advice": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "action", "rationale"],
                "properties": {
                    "title": {
                        "type": "string",
                        "maxLength": 80,
                        "description": "Brief title for budget improvement action"
                    },
                    "action": {
                        "type": "string",
                        "maxLength": 250,
                        "description": "Specific, actionable step to take"
                    },
                    "rationale": {
                        "type": "string",
                        "maxLength": 300,
                        "description": "Why this action matters for the user"
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Priority level (1=highest, 5=lowest)"
                    }
                }
            },
            "minItems": 1,
            "maxItems": 5,
            "description": "Budget improvement recommendations"
        },
        "debt_strategy": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "action", "rationale"],
                "properties": {
                    "title": {
                        "type": "string",
                        "maxLength": 80
                    },
                    "action": {
                        "type": "string",
                        "maxLength": 250
                    },
                    "rationale": {
                        "type": "string",
                        "maxLength": 300
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5
                    }
                }
            },
            "minItems": 1,
            "maxItems": 5,
            "description": "Debt repayment strategy and actions"
        },
        "investment_strategy": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "action", "rationale"],
                "properties": {
                    "title": {
                        "type": "string",
                        "maxLength": 80
                    },
                    "action": {
                        "type": "string",
                        "maxLength": 250
                    },
                    "rationale": {
                        "type": "string",
                        "maxLength": 300
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5
                    }
                }
            },
            "minItems": 1,
            "maxItems": 5,
            "description": "Investment diversification strategy"
        },
        "goal_roadmap": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "action", "rationale"],
                "properties": {
                    "title": {
                        "type": "string",
                        "maxLength": 80
                    },
                    "action": {
                        "type": "string",
                        "maxLength": 250
                    },
                    "rationale": {
                        "type": "string",
                        "maxLength": 300
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5
                    }
                }
            },
            "minItems": 1,
            "maxItems": 5,
            "description": "Step-by-step roadmap to achieve financial goals"
        },
        "risk_explanation": {
            "type": "string",
            "maxLength": 500,
            "description": "Clear explanation of risk factors and important disclaimers"
        },
        "human_summary": {
            "type": "string",
            "maxLength": 400,
            "description": "Human-friendly summary of key recommendations in plain language"
        }
    },
    "additionalProperties": False
}


# ============================================================================
# FORBIDDEN PHRASES - PREVENT GUARANTEED RETURN PROMISES
# ============================================================================

FORBIDDEN_PHRASES = [
    r"guaranteed return",
    r"guarantee of return",
    r"promise of returns",
    r"assured return",
    r"certain return",
    r"will definitely return",
    r"will certainly return",
    r"risk-free return",
    r"will surely return",
    r"guaranteed profit",
    r"promise of profit",
]


# ============================================================================
# PROMPT BUILDER
# ============================================================================

def build_contextual_prompt(report: Dict[str, Any]) -> str:
    """Build comprehensive Gemini prompt from financial report.
    
    Extracts all relevant financial context and builds a structured prompt
    that guides Gemini to provide specific, actionable financial advice across
    4 key areas: budget, debt, investments, and goals.
    
    Args:
        report: Complete financial report from build_user_report()
                Must contain: user_profile, financial_snapshot, computed_metrics,
                holdings_summary, goals_analysis, spending_analysis,
                advanced_spending_analysis, goal_planning, portfolio_recommendation
        
    Returns:
        str: Structured prompt for Gemini API
        
    Raises:
        ValueError: If required report sections are missing
    """
    
    # Validate required sections
    required_sections = [
        'user_profile', 'financial_snapshot', 'computed_metrics',
        'holdings_summary', 'goals_analysis', 'spending_analysis',
        'portfolio_recommendation'
    ]
    
    for section in required_sections:
        if section not in report:
            raise ValueError(f"Report missing required section: {section}")
    
    # Extract data from report
    user_profile = report.get('user_profile', {})
    financial_snapshot = report.get('financial_snapshot', {})
    computed_metrics = report.get('computed_metrics', {})
    holdings_summary = report.get('holdings_summary', {})
    goals_analysis = report.get('goals_analysis', {})
    spending_analysis = report.get('spending_analysis', {})
    advanced_analysis = report.get('advanced_spending_analysis', {})
    goal_planning = report.get('goal_planning', {})
    portfolio_recommendation = report.get('portfolio_recommendation', {})
    
    # Build prompt sections
    prompt_sections = []
    
    # 1. PREAMBLE - Set expectations and constraints
    preamble = """You are an expert financial advisor providing personalized financial guidance.

CRITICAL INSTRUCTIONS:
1. NEVER promise guaranteed returns or guaranteed profits
2. NEVER suggest "risk-free" investments
3. ALWAYS include appropriate risk disclaimers
4. ALWAYS base recommendations on the user's specific financial situation
5. PROVIDE actionable, specific advice (not generic)
6. ALWAYS output VALID JSON matching the required schema

Return ONLY valid JSON - no markdown, no code blocks, no explanation text."""
    
    prompt_sections.append(preamble)
    
    # 2. USER CONTEXT
    user_context = _build_user_context_section(user_profile, financial_snapshot)
    prompt_sections.append(user_context)
    
    # 3. FINANCIAL HEALTH ANALYSIS
    health_analysis = _build_health_analysis_section(
        computed_metrics, financial_snapshot
    )
    prompt_sections.append(health_analysis)
    
    # 4. SPENDING PATTERNS
    spending_context = _build_spending_context_section(
        spending_analysis, advanced_analysis
    )
    prompt_sections.append(spending_context)
    
    # 5. CURRENT PORTFOLIO
    portfolio_context = _build_portfolio_context_section(
        holdings_summary, portfolio_recommendation
    )
    prompt_sections.append(portfolio_context)
    
    # 6. FINANCIAL GOALS
    goals_context = _build_goals_context_section(goals_analysis, goal_planning)
    prompt_sections.append(goals_context)
    
    # 7. REQUEST FOR ADVICE
    advice_request = _build_advice_request_section()
    prompt_sections.append(advice_request)
    
    # 8. OUTPUT SCHEMA SPECIFICATION
    schema_spec = _build_schema_specification()
    prompt_sections.append(schema_spec)
    
    return "\n\n".join(prompt_sections)


def _build_user_context_section(user_profile: Dict[str, Any], financial_snapshot: Dict[str, Any]) -> str:
    """Build user context and financial snapshot section."""
    
    age = "Unknown"
    if user_profile.get('date_of_birth'):
        try:
            dob = datetime.fromisoformat(user_profile['date_of_birth'])
            age = (datetime.utcnow() - dob).days // 365
        except:
            pass
    
    return f"""## USER PROFILE AND CURRENT FINANCIAL SITUATION

User: {user_profile.get('name', 'Unknown')}
Age: {age} years
Location: {user_profile.get('country', 'Unknown')}
Member Since: {user_profile.get('member_since', 'Unknown')}

### Current Financial Position
Period: {financial_snapshot.get('period', 'N/A')}
- Monthly Income: ₹{financial_snapshot.get('total_income', 0):,.2f}
- Monthly Expenses: ₹{financial_snapshot.get('total_expenses', 0):,.2f}
- Monthly Savings: ₹{financial_snapshot.get('total_savings', 0):,.2f}
- Total Net Worth: ₹{financial_snapshot.get('net_worth', 0):,.2f}
- Total Investments: ₹{financial_snapshot.get('total_investments', 0):,.2f}"""


def _build_health_analysis_section(computed_metrics: Dict[str, float], financial_snapshot: Dict[str, Any]) -> str:
    """Build financial health metrics section."""
    
    savings_rate = computed_metrics.get('savings_rate', 0.0)
    dti = computed_metrics.get('debt_to_income_ratio', 0.0)
    emergency_fund = computed_metrics.get('emergency_fund_months', 0.0)
    investment_ratio = computed_metrics.get('investment_ratio', 0.0)
    
    # Financial health assessment
    health_status = "Needs Improvement"
    if savings_rate >= 0.20 and emergency_fund >= 6:
        health_status = "Good"
    elif savings_rate >= 0.10 and emergency_fund >= 3:
        health_status = "Fair"
    
    return f"""## FINANCIAL HEALTH METRICS

- Savings Rate: {savings_rate*100:.1f}% (target: 20%+)
- Debt-to-Income Ratio: {dti:.2%}
- Emergency Fund: {emergency_fund:.1f} months of expenses (target: 6 months)
- Investment Ratio: {investment_ratio:.2%} (% of net worth in investments)
- Overall Health Status: {health_status}

Key Observations:
- Current savings capacity: ₹{computed_metrics.get('monthly_savings', 0):,.2f}/month
- Monthly income: ₹{computed_metrics.get('monthly_income', 0):,.2f}
- Monthly expenses: ₹{computed_metrics.get('monthly_expenses', 0):,.2f}"""


def _build_spending_context_section(spending_analysis: Dict[str, Any], advanced_analysis: Dict[str, Any]) -> str:
    """Build spending patterns and analysis section."""
    
    # Extract top spending categories
    high_spending = advanced_analysis.get('high_spending_categories', {})
    subscriptions = advanced_analysis.get('recurring_subscriptions', {})
    
    high_categories = ""
    if high_spending:
        top_cats = sorted(
            high_spending.items(),
            key=lambda x: x[1].get('percentage', 0),
            reverse=True
        )[:3]
        high_categories = "\nTop Spending Categories:"
        for cat, data in top_cats:
            pct = data.get('percentage', 0)
            high_categories += f"\n  - {cat}: {pct:.1f}% of budget"
    
    recurring = ""
    if subscriptions:
        recurring = "\nRecurring Subscriptions (potential savings opportunities):"
        for sub, amount in list(subscriptions.items())[:5]:
            recurring += f"\n  - {sub}: ₹{amount:,.2f}"
    
    budget_ratio = spending_analysis.get('budget_ratio', 0.0)
    budget_health = "Balanced"
    if budget_ratio > 0.9:
        budget_health = "Critical - Over budget"
    elif budget_ratio > 0.75:
        budget_health = "Tight - Watch spending"
    
    return f"""## SPENDING ANALYSIS

Budget Status: {budget_health}
- Budget Utilization: {budget_ratio*100:.1f}% of income {high_categories}{recurring}

Spending Insights:
- Analyze opportunities to reduce discretionary spending
- Consider automating necessary expenses
- Identify and consolidate overlapping subscriptions"""


def _build_portfolio_context_section(holdings_summary: Dict[str, Any], portfolio_recommendation: Dict[str, Any]) -> str:
    """Build current portfolio and recommendations section."""
    
    current_allocation = holdings_summary.get('asset_allocation_pct', {})
    recommended = portfolio_recommendation.get('recommended_portfolio', {})
    
    current_str = ""
    if current_allocation:
        current_str = "\nCurrent Allocation:\n"
        for asset_class, pct in current_allocation.items():
            current_str += f"  - {asset_class}: {pct:.1f}%\n"
    
    recommended_str = ""
    if recommended:
        recommended_str = "\nRecommended Allocation:\n"
        for asset_class, pct in recommended.items():
            recommended_str += f"  - {asset_class}: {pct:.1f}%\n"
    
    instruments = portfolio_recommendation.get('asset_class_instruments', {})
    instruments_str = ""
    if instruments:
        instruments_str = "\nRecommended Instruments:\n"
        for asset_class, items in instruments.items():
            if isinstance(items, list):
                instruments_str += f"  {asset_class.title()}:\n"
                for item in items[:2]:  # Top 2 per class
                    if isinstance(item, dict):
                        instruments_str += f"    - {item.get('name', 'N/A')}\n"
    
    return f"""## PORTFOLIO & INVESTMENT POSITION

Current Holdings: {holdings_summary.get('count', 0)} positions
Portfolio Value: ₹{holdings_summary.get('total_value', 0):,.2f}{current_str}{recommended_str}{instruments_str}"""


def _build_goals_context_section(goals_analysis: Dict[str, Any], goal_planning: Dict[str, Any]) -> str:
    """Build financial goals section."""
    
    goals_list = goals_analysis.get('goals', [])
    
    goals_summary = ""
    if goals_list:
        goals_summary = "\nActive Goals:\n"
        for goal in goals_list[:5]:  # Top 5 goals
            goal_name = goal.get('goal_name', 'Goal')
            target = goal.get('target_amount', 0)
            deadline = goal.get('target_date', 'N/A')
            achieved = goal.get('amount_accumulated', 0)
            progress = (achieved / target * 100) if target > 0 else 0
            
            goals_summary += f"  - {goal_name}: ₹{target:,.0f} (Deadline: {deadline}, Progress: {progress:.0f}%)\n"
    
    planning_context = goal_planning.get('strategies', [])
    planning_str = ""
    if planning_context:
        planning_str = "\nGoal Strategies Recommended:\n"
        for strategy in planning_context[:3]:
            if isinstance(strategy, dict):
                planning_str += f"  - {strategy.get('strategy_name', 'Strategy')}\n"
    
    return f"""## FINANCIAL GOALS & PLANNING{goals_summary}{planning_str}

Goal Achievement Priority: Focus on goals based on timeline and importance
- Short-term (< 1 year): Priority for capital preservation
- Medium-term (1-5 years): Balance growth and safety
- Long-term (5+ years): Can tolerate higher volatility for growth"""


def _build_advice_request_section() -> str:
    """Build the request for specific advice."""
    
    return """## REQUESTED FINANCIAL ADVICE

Based on this user's complete financial profile, provide structured advice in FOUR areas:

1. **BUDGET IMPROVEMENT** - Specific ways to optimize income vs expenses
   - Identify highest impact spending reductions
   - Suggest budget optimization strategies
   - Recommend automation opportunities

2. **DEBT REPAYMENT STRATEGY** - If applicable, create a debt elimination plan
   - Prioritize debts by interest rate and impact
   - Suggest repayment acceleration methods
   - Calculate impact on overall finances

3. **INVESTMENT DIVERSIFICATION STRATEGY** - Optimize asset allocation
   - Asset class rebalancing recommendations
   - Specific instrument suggestions that align with goals
   - Risk-adjusted portfolio construction
   - Consider investment horizon and goals

4. **GOAL ACHIEVEMENT ROADMAP** - Step-by-step plan to achieve financial goals
   - Prioritize goals based on feasibility and importance
   - Calculate required monthly contributions
   - Identify timeline and milestones
   - Connect specific goals to investment strategy

CRITICAL CONSTRAINTS:
- NEVER promise or guarantee specific returns
- ALWAYS include risk disclaimers
- MUST be specific and actionable (not generic advice)
- Focus on high-impact, practical steps
- Align recommendations with the user's risk tolerance and timeline"""


def _build_schema_specification() -> str:
    """Build the output schema specification for the model."""
    
    schema_json = json.dumps(CONTEXTUAL_OUTPUT_SCHEMA, indent=2)
    
    return f"""## OUTPUT REQUIREMENTS

Return ONLY valid JSON (no markdown, no explanation) matching this exact schema:

{schema_json}

IMPORTANT NOTES:
- All text fields must be strings, not arrays
- All arrays with action items must have 1-5 items minimum
- Each action must have title, action, and rationale fields
- Action items must be specific and actionable
- Include priority (1-5) where possible
- risk_explanation MUST include appropriate disclaimers
- human_summary should be plain language explanation for non-financial users"""


# ============================================================================
# VALIDATION AND FILTERING
# ============================================================================

def validate_contextual_output(response_json: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Validate contextual advice response against schema.
    
    Args:
        response_json: JSON response from Gemini
        
    Returns:
        tuple: (parsed_dict or None, error_message or None)
    """
    try:
        # Parse JSON
        parsed = json.loads(response_json)
        
        # Validate against schema
        jsonschema.validate(instance=parsed, schema=CONTEXTUAL_OUTPUT_SCHEMA)
        
        # Additional validation: check for forbidden phrases
        response_str = json.dumps(parsed).lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in response_str:
                return None, f"Response contains forbidden phrase: '{phrase}'"
        
        # Verify risk warning is present and substantial
        risk_explanation = parsed.get('risk_explanation', '').lower()
        if not risk_explanation or len(risk_explanation) < 50:
            return None, "Risk explanation too brief or missing - must include proper disclaimers"
        
        return parsed, None
        
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {str(e)}"
    except jsonschema.ValidationError as e:
        return None, f"Schema validation failed: {e.message}"


def generate_contextual_fallback_advice(report: Dict[str, Any]) -> Dict[str, Any]:
    """Generate deterministic fallback advice when Gemini unavailable.
    
    Args:
        report: Financial report dict
        
    Returns:
        dict: Structured advice matching output schema
    """
    
    metrics = report.get('computed_metrics', {})
    financial = report.get('financial_snapshot', {})
    goals = report.get('goals_analysis', {})
    spending = report.get('spending_analysis', {})
    
    # Analyze user's situation
    savings_rate = metrics.get('savings_rate', 0.0)
    dti = metrics.get('debt_to_income_ratio', 0.0)
    emergency_fund = metrics.get('emergency_fund_months', 0.0)
    
    # Generate context-appropriate fallback advice
    budget_advice = []
    debt_strategy = []
    investment_strategy = []
    goal_roadmap = []
    
    # Budget advice based on metrics
    if savings_rate < 0.10:
        budget_advice.append({
            "title": "Increase Savings Rate to 10-20%",
            "action": "Review monthly expenses and identify categories to reduce by 10-15%. Automate savings to a separate account before spending.",
            "rationale": "Current savings rate is below recommended 20%. This limits your ability to invest and build emergency fund.",
            "priority": 1
        })
    
    if emergency_fund < 3:
        budget_advice.append({
            "title": "Build Emergency Fund",
            "action": "Target 6 months of living expenses in liquid savings. Start with 1 month and increase gradually.",
            "rationale": "Emergency fund protects against unexpected expenses without derailing financial goals.",
            "priority": 1
        })
    
    # Debt strategy
    if dti > 0.3:
        debt_strategy.append({
            "title": "Prioritize High-Interest Debt",
            "action": "Identify debts by interest rate. Focus extra payments on highest rate debts first (avalanche method).",
            "rationale": "High debt-to-income ratio limits borrowing capacity and increases financial stress.",
            "priority": 1
        })
    
    # Investment strategy
    investment_strategy.append({
        "title": "Diversify Across Asset Classes",
        "action": "Ensure allocation across equity (growth), debt (stability), and gold (hedge) based on your risk tolerance and timeline.",
        "rationale": "Diversification reduces volatility and improves risk-adjusted returns over time.",
        "priority": 2
    })
    
    # Goal roadmap
    if goals.get('goals'):
        goal_roadmap.append({
            "title": "Align Investments with Goal Timeline",
            "action": "For short-term goals (< 3 years), allocate to low-risk debt/bonds. For long-term goals, can use higher equity allocation.",
            "rationale": "Time horizon determines appropriate risk level. Longer timelines can weather market volatility.",
            "priority": 1
        })
    
    return {
        "budget_advice": budget_advice or [{
            "title": "Optimize Monthly Budget",
            "action": "Track all expenses for 1 month to identify largest spending categories. Target 10-15% reduction in variable expenses.",
            "rationale": "Budget optimization improves savings rate and accelerates progress toward financial goals.",
            "priority": 2
        }],
        "debt_strategy": debt_strategy or [{
            "title": "Monitor and Maintain Healthy Debt Levels",
            "action": "Keep debt-to-income ratio below 30%. Avoid new debt unless for productive assets (education, home).",
            "rationale": "Low debt levels improve financial flexibility and reduce financial stress.",
            "priority": 2
        }],
        "investment_strategy": investment_strategy,
        "goal_roadmap": goal_roadmap or [{
            "title": "Create Specific, Measurable Goals",
            "action": "Define goals with clear amounts and timelines. Calculate required monthly savings to achieve each goal.",
            "rationale": "Specific goals with timelines enable better planning and progress tracking.",
            "priority": 2
        }],
        "risk_explanation": "All investments carry risk, including potential loss of principal. Past performance does not guarantee future results. Asset allocation and diversification do not ensure profit or protect against loss. Consider your risk tolerance, investment timeline, and financial goals when making investment decisions. This advice is educational and not a substitute for personalized financial guidance from a qualified advisor.",
        "human_summary": "Focus on building an emergency fund while gradually increasing your investment allocation across diversified assets. Automate savings to make financial progress consistent and easier. Align your investment strategy with your specific goals and timeline. Regularly review and rebalance your portfolio."
    }
