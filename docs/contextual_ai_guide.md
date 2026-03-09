"""Contextual Prompt Builder - Complete Integration Guide

Integrates all financial data into comprehensive AI advice generation.

Module: backend/ai/contextual_prompt.py
Updated: backend/ai/ai_client.py
Test: test_contextual_ai.py

========================================
OVERVIEW
========================================

The contextual prompt builder creates intelligent Gemini prompts by combining
ALL financial data into a single, comprehensive prompt that guides the model
to provide specific, actionable advice across 4 key areas:

1. BUDGET IMPROVEMENT - Budget optimization and spending reduction
2. DEBT REPAYMENT STRATEGY - Debt elimination planning (if applicable)
3. INVESTMENT DIVERSIFICATION - Asset allocation and instrument selection
4. GOAL ACHIEVEMENT ROADMAP - Step-by-step goal achievement planning

Output is structured JSON with validation and content filtering to prevent
guaranteed return promises.

========================================
ARCHITECTURE
========================================

Input: Financial Report (from build_user_report)
  ├── user_profile
  ├── financial_snapshot
  ├── computed_metrics
  ├── holdings_summary
  ├── goals_analysis
  ├── spending_analysis
  ├── advanced_spending_analysis
  ├── goal_planning
  └── portfolio_recommendation

Process:
  1. Validate all required sections present
  2. Extract key financial context
  3. Build structured Gemini prompt with:
     - Preamble (constraints and expectations)
     - User context (profile + finances)
     - Health analysis (metrics interpretation)
     - Spending patterns (insights)
     - Portfolio context (current + recommended)
     - Goals context (timeline + progress)
     - Advice request (4 areas)
     - Output schema specification (JSON structure)
  4. Call Gemini with combined context
  5. Validate response against schema
  6. Check for forbidden phrases (guaranteed returns)
  7. Validate risk explanation is substantive
  8. Return validated advice

Output: Structured Advice JSON
  {
    "budget_advice": [
      {
        "title": "Specific action title",
        "action": "Details of what to do",
        "rationale": "Why it matters",
        "priority": 1-5
      }, ...
    ],
    "debt_strategy": [...],
    "investment_strategy": [...],
    "goal_roadmap": [...],
    "risk_explanation": "Comprehensive disclaimers...",
    "human_summary": "Plain language summary..."
  }

========================================
USAGE
========================================

Method 1: Using Convenience Function

  from backend.ai.ai_client import generate_contextual_advice
  from backend.finance.report_builder import build_user_report
  
  # Build complete report
  report = build_user_report(user_id, db)
  
  # Generate contextual advice
  advice = generate_contextual_advice(report)
  
  # Access advice sections
  for item in advice['budget_advice']:
    print(f"{item['title']}: {item['action']}")


Method 2: Using ContextualAIClient Class

  from backend.ai.ai_client import ContextualAIClient
  
  client = ContextualAIClient()
  advice = client.generate_contextual_advice(report)


Method 3: Manual Prompt Building

  from backend.ai.contextual_prompt import (
    build_contextual_prompt,
    validate_contextual_output,
  )
  
  # Build prompt manually
  prompt = build_contextual_prompt(report)
  
  # Send to Gemini
  response = gemini_client.generate(prompt)
  
  # Validate
  advice, error = validate_contextual_output(response)

========================================
OUTPUT SCHEMA
========================================

Required Fields:
  - budget_advice: Array of budget improvement recommendations
  - debt_strategy: Array of debt repayment actions
  - investment_strategy: Array of investment recommendations
  - goal_roadmap: Array of goal achievement steps
  - risk_explanation: String (min 50 chars) with disclaimers
  - human_summary: String summary for non-experts

Each Action Item Has:
  - title: Brief action title (max 80 chars) - REQUIRED
  - action: Specific, actionable step (max 250 chars) - REQUIRED
  - rationale: Why this matters for user (max 300 chars) - REQUIRED
  - priority: 1-5 (optional, 1=highest)

Array Constraints:
  - Each section must have 1-5 items (1+ required, max 5)
  - All text must be strings
  - Additional properties not allowed

Risk Explanation Constraints:
  - Minimum 50 characters
  - MUST include disclaimers
  - Cannot promise guaranteed returns
  - Cannot suggest "risk-free" investments

========================================
CONTENT VALIDATION
========================================

Forbidden Phrases (prevent return promises):
  ✗ "guaranteed return"
  ✗ "guarantee of return"
  ✗ "promise of returns"
  ✗ "assured return"
  ✗ "certain return"
  ✗ "will definitely return"
  ✗ "risk-free return"
  ✗ "guaranteed profit"
  ✗ "promise of profit"

Allowed:
  ✓ "does not guarantee"
  ✓ "not guaranteed"
  ✓ "no guarantee"
  ✓ "risk-adjusted returns"
  ✓ "expected returns"
  ✓ "historical returns"

Risk Statement Examples (REQUIRED):
  ✓ "All investments carry risk, including loss of principal. Past performance 
    does not guarantee future results."
  ✓ "Investment returns are not guaranteed. Market conditions may result in losses."
  ✓ "Diversification does not ensure profit or protect against loss."

========================================
FALLBACK ADVICE GENERATION
========================================

When Gemini unavailable, module generates deterministic fallback advice based
on user's financial situation:

Triggers:
  - Gemini API not available
  - Gemini API timeout/error
  - Response validation failure
  - Content filtering rejection

Logic:
  1. Analyze user's metrics (savings_rate, debt-to-income, emergency_fund)
  2. Generate context-appropriate recommendations:
     - Low savings rate → Prioritize budget cuts
     - Low emergency fund → Build reserves first
     - High debt → Debt payoff strategy
     - Active goals → Timeline-based roadmap
  3. Include comprehensive risk disclaimers
  4. Return valid JSON matching schema

Examples:

  If savings_rate < 10%:
    ✓ "Review monthly expenses and identify categories to reduce by 10-15%.
      Automate savings to separate account."
  
  If emergency_fund < 3 months:
    ✓ "Target 6 months of living expenses in liquid savings.
      Start with 1 month and increase gradually."
  
  If debt_to_income > 30%:
    ✓ "Focus extra payments on highest rate debts first (avalanche method).
      This improves debt-to-income ratio and frees up cash flow."

========================================
CACHING
========================================

Responses are cached by prompt hash for 5 minutes:

  Cache Key: SHA256(prompt_text)
  TTL: 300 seconds (5 minutes)
  Storage: In-memory dict ({prompt_hash: (response, timestamp)})

Same user → Same financial data → Same prompt hash → Cached response
(Reduces Gemini API calls and improves response time)

Manual Cache Clear:
  
  client = ContextualAIClient()
  client._cache.clear()

========================================
AUDIT LOGGING
========================================

Every contextual advice call is logged:

  Logged Information:
    - user_id
    - model_used (gemini, local-fallback, cache)
    - model_version (e.g., "gemini-pro", "fallback-contextual-v1")
    - template_used (always "contextual")
    - input_report (full report dict)
    - prompt (full prompt text)
    - raw_model_response (before validation)
    - validated_response (after validation)
    - validation_errors (if any)
    - timestamp
    - call_duration

Access Logs:
  
  from backend.ai.audit import get_audit_logger
  
  audit_logger = get_audit_logger()
  logs = audit_logger.get_user_history("user-id-123")

========================================
INTEGRATION POINTS
========================================

1. Financial Report API
   
   GET /api/reports/{user_id}
   └─ Now includes portfolio_recommendation section
      Used by contextual_prompt builder

2. AI Advice API (NEW)
   
   GET /api/advice/{user_id}?type=contextual
   └─ Returns contextual advice with 4 areas
      Uses generate_contextual_advice()

3. Dashboard Integration
   
   Display advice sections as:
   - Budget Tips Card
   - Debt Strategy Card
   - Investment Strategy Card  
   - Goal Roadmap Card
   - Risk/Disclaimer section

========================================
ERROR HANDLING
========================================

Scenario: Missing Report Sections

  try:
    advice = generate_contextual_advice(incomplete_report)
  except ValueError as e:
    # Report missing required section
    # e.g., "Report missing required section: portfolio_recommendation"
    print(f"Invalid report: {e}")


Scenario: Gemini API Failure

  Input: Valid report + No Gemini API
  Process: Automatic fallback to deterministic advice
  Output: Valid contextual advice (fallback version)
  User Impact: Seamless - no error returned


Scenario: Response Validation Failure

  Input: Gemini returns invalid JSON
  Process: Automatically use fallback advice
  Output: Valid contextual advice (fallback version)
  Logged: Validation error + fallback flag


Scenario: Forbidden Content Detected

  Input: Response contains "guaranteed 10% return"
  Process: Reject response + use fallback
  Output: Safe fallback advice
  Logged: Content filter rejection reason


========================================
CUSTOMIZATION
========================================

To customize contextual prompt:

1. Edit PREAMBLE section for model instructions
2. Edit _build_user_context_section() for user data emphasis
3. Edit _build_health_analysis_section() for metric interpretation
4. Edit _build_advice_request_section() for advice areas/priority
5. Modify FORBIDDEN_PHRASES for content policy
6. Extend CONTEXTUAL_OUTPUT_SCHEMA for new fields

To customize fallback logic:

1. Edit generate_contextual_fallback_advice()
2. Adjust decision thresholds for metrics
3. Add new recommendation templates
4. Modify action priority levels

========================================
TESTING
========================================

Unit Tests:

  python test_contextual_ai.py
  
  Tests:
    ✓ Module imports
    ✓ Prompt generation from sample report
    ✓ Schema validation (valid response)
    ✓ Content filtering (forbidden phrases)
    ✓ Fallback advice generation
    ✓ AI client instantiation and usage

Integration Tests:

  pytest tests/test_contextual_ai_integration.py -v
  
  Tests:
    ✓ Full workflow: report → prompt → Gemini → validation
    ✓ Report with missing sections (error handling)
    ✓ Cache hits and misses
    ✓ Fallback activation
    ✓ Audit logging
    ✓ Risk explanation validation
    ✓ Content filtering edge cases

Performance Tests:

  Prompt generation: < 50ms
  Schema validation: < 5ms
  Fallback generation: < 10ms
  Gemini call (with network): 1-5 seconds
  Cache hit response: < 1ms

========================================
METRICS & MONITORING
========================================

Track in production:

  1. Response Times
     - Prompt generation time
     - Gemini API response time
     - Total generation time (with validation)

  2. Model Usage
     - % Gemini responses
     - % Fallback responses
     - % Cache hits
     - % Validation failures
     - % Content filter rejections

  3. Quality Metrics
     - User satisfaction (if survey available)
     - Actionability of advice (user engagement)
     - Follow-through rate on recommendations

  4. Error Tracking
     - Validation failure reasons
     - Content filter rejection types
     - Gemini API error types

Sample Monitoring Query:

  SELECT 
    DATE(timestamp) as date,
    model_used,
    COUNT(*) as calls,
    AVG(call_duration_ms) as avg_duration
  FROM ai_audit_log
  WHERE template_used = 'contextual'
  GROUP BY DATE(timestamp), model_used

========================================
DEPLOYMENT CHECKLIST
========================================

Before deploying to production:

  ✓ All tests passing (unit + integration)
  ✓ Content filtering properly blocking dangerous phrases
  ✓ Risk disclaimers present in all responses
  ✓ Fallback advice generation working
  ✓ Cache working and improving latency
  ✓ Audit logging functional
  ✓ Error handling tested (all scenarios)
  ✓ Performance acceptable (< 5s end-to-end)
  ✓ Gemini API key configured in environment
  ✓ Documentation updated
  ✓ API endpoints created for advice access
  ✓ Dashboard integration planned

========================================
FUTURE ENHANCEMENTS
========================================

Potential improvements:

1. Multi-model Support
   - Support Claude, GPT-4 in addition to Gemini
   - Router to select best model for context

2. Follow-up Advice
   - Track which advice items user followed
   - Provide follow-up recommendations
   - Personalization based on user behavior

3. Real-time Data Integration
   - Pull live market data
   - Current interest rates
   - Inflation projections
   - Personalized instrument recommendations

4. Goal-Specific Advice
   - Generate advice customized per goal
   - Timeline-specific strategies
   - Goal-to-portfolio mapping

5. Feedback Loop
   - User rates advice usefulness
   - Model retraining on feedback
   - Continuous improvement

6. Explainability
   - Why this advice (reasoning chain)
   - Data sources for recommendations
   - Confidence levels

========================================
SUPPORT & TROUBLESHOOTING
========================================

Issue: "Report missing required section"

  Solution: Ensure build_user_report() includes all sections:
    - user_profile ✓
    - financial_snapshot ✓
    - computed_metrics ✓
    - holdings_summary ✓
    - goals_analysis ✓
    - spending_analysis ✓
    - portfolio_recommendation ✓


Issue: "Schema validation failed"

  Solution: Check Gemini response format
    - Must be valid JSON
    - All required fields present
    - No extra fields allowed
    - Array items must have title, action, rationale


Issue: "Risk explanation too brief"

  Solution: Ensure risk_explanation is:
    - At least 50 characters
    - Includes disclaimers (not guaranteed, loss of principal, etc.)
    - Not just a single sentence


Issue: "Content blocked"

  Solution: Check for forbidden phrases:
    ✗ "guaranteed return"
    ✗ "risk-free"
    ✓ Use "expected return" instead
    ✓ Include "does not guarantee" in disclaimers


Issue: Slow response times

  Solution:
    - Check cache hit rate (should be > 50%)
    - Enable Gemini caching
    - Consider async/batch processing
    - Monitor Gemini API latency

========================================
"""

print(__doc__)
