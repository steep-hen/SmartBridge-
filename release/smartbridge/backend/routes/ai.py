"""AI advice generation endpoints.

Provides AI-powered financial advice for users.

Endpoints:
    POST /ai/advice/{user_id} - Generate AI advice (protected)
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import verify_api_key
from backend.config import settings
from backend.db import get_db
from backend.models import User
from backend.routes.reports import generate_financial_report
from backend.schemas import AIAdviceRequest, AIAdviceResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/ai", tags=["ai"])

# Local advice templates (fallback when no Gemini API)
LOCAL_ADVICE_TEMPLATES = [
    "Based on your expense patterns, consider reducing discretionary spending categories. Calculate your average monthly spending and identify areas where you could cut back by 5-10%.",
    "Your income-to-savings ratio suggests you could increase your investment contributions. Consider automating monthly transfers to an investment account.",
    "Review your recurring expenses monthly. Many users find they can save 10-15% by eliminating unused subscriptions.",
    "Consider creating a budget-tracking system if you haven't already. Tracking expenses by category helps identify spending patterns.",
    "Build an emergency fund equivalent to 3-6 months of expenses. This provides financial security and reduces need for high-interest debt.",
    "Diversify your investment portfolio across different asset classes. Most advisors recommend a mix suitable to your risk tolerance and time horizon.",
    "Review your financial goals quarterly. Adjust targets as your income or circumstances change.",
    "Consider tax-advantaged investment accounts for long-term wealth building. Speak with a tax professional about options.",
]


def get_local_advice(user_id: UUID) -> str:
    """Generate local advice without AI.
    
    Returns sensible general financial advice.
    """
    import hashlib
    
    # Use user ID to select deterministic advice
    hash_val = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
    index = hash_val % len(LOCAL_ADVICE_TEMPLATES)
    
    return LOCAL_ADVICE_TEMPLATES[index]


async def generate_gemini_advice(
    user_id: UUID,
    question: str,
    report_summary: dict,
    db: Session,
) -> str:
    """Generate advice using Gemini API.
    
    Args:
        user_id: User ID
        question: User question
        report_summary: Financial report data
        db: Database session
    
    Returns:
        AI-generated advice
    """
    if not settings.has_gemini_api_key:
        return get_local_advice(user_id)
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-pro")
        
        # Build context
        context = f"""You are a financial advisor. Provide personalized advice based on this user's financial profile:

Income: ${report_summary.get('total_income', 0):.2f}
Expenses: ${report_summary.get('total_expenses', 0):.2f}
Savings Rate: {report_summary.get('savings_rate', 0):.1f}%
Net Worth: ${report_summary.get('net_worth', 0):.2f}
Investment Value: ${report_summary.get('investment_value', 0):.2f}

User Question: {question}

Provide practical, actionable financial advice in 2-3 sentences."""
        
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        # Fall back to local advice on any API error
        return get_local_advice(user_id)


@router.post("/advice/{user_id}", response_model=AIAdviceResponse)
async def generate_ai_advice(
    user_id: UUID,
    request: AIAdviceRequest,
    api_authenticated: bool = Depends(verify_api_key),
    db: Session = Depends(get_db),
):
    """
    Generate AI financial advice for user.
    
    Protected endpoint requiring API key authentication.
    Uses Google Gemini API if available, falls back to local advice.
    
    Args:
        user_id: User ID
        request: Advice request with optional question
        api_authenticated: API key verification (required)
        db: Database session
    
    Returns:
        AI-generated financial advice
    
    Raises:
        HTTPException: 401 if not authenticated, 404 if user not found
    
    Example:
        POST /ai/advice/123e4567-e89b-12d3-a456-426614174000
        Header: X-API-KEY: your-secret-key
        {
            "question": "How can I improve my savings rate?",
            "include_report": true
        }
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )
    
    # Generate financial report for context
    report = await generate_financial_report(user_id, db)
    
    report_summary = {
        "total_income": report.total_income,
        "total_expenses": report.total_expenses,
        "savings_rate": report.savings_rate,
        "net_worth": report.net_worth,
        "investment_value": report.investment_value,
    }
    
    # Determine advice source and generate
    source = "gemini" if settings.has_gemini_api_key else "local"
    
    if request.question:
        advice = await generate_gemini_advice(
            user_id,
            request.question,
            report_summary,
            db,
        )
    else:
        advice = get_local_advice(user_id)
    
    return AIAdviceResponse(
        user_id=user_id,
        advice=advice,
        confidence=0.85 if source == "gemini" else 0.60,
        generated_at=datetime.utcnow(),
        source=source,
    )
