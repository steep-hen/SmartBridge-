"""
Pydantic schemas for request/response validation.

Separates API contracts from ORM models.
Request schemas for POST/PUT operations with validation.
Response schemas for GET operations with serialization.

Includes:
- Validation rules (email format, positive amounts, date constraints)
- Optional nested relationships for detailed responses
- Proper datetime serialization
- Docstrings for API documentation
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, validator, root_validator


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserCreate(BaseModel):
    """Request schema for creating a new user."""
    email: EmailStr = Field(..., description="Email address (unique)")
    name: str = Field(..., min_length=1, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Birth date")
    gender: Optional[str] = Field(None, pattern=r"^[MFO]?$", description="Gender (M/F/O)")
    country: Optional[str] = Field(None, max_length=100, description="Country")

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "phone": "+1-555-1234",
                "gender": "M",
                "country": "United States"
            }
        }


class UserResponse(BaseModel):
    """Response schema for user detail."""
    id: UUID
    email: str
    name: str
    phone: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    country: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "phone": "+1-555-1234",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-02T15:30:00"
            }
        }


class UserDetailResponse(UserResponse):
    """Extended response with financial summary, holdings, and goals."""
    financial_summaries: Optional[List['FinancialSummaryResponse']] = []
    holdings: Optional[List['HoldingResponse']] = []
    goals: Optional[List['GoalResponse']] = []

    class Config:
        from_attributes = True


# ============================================================================
# FINANCIAL_SUMMARY SCHEMAS
# ============================================================================

class FinancialSummaryCreate(BaseModel):
    """Request schema for creating financial summary."""
    year: int = Field(..., ge=2000, le=2100, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    total_income: float = Field(0, ge=0, description="Total income")
    total_expenses: float = Field(0, ge=0, description="Total expenses")
    total_savings: float = Field(0, ge=0, description="Total savings")
    total_investments: float = Field(0, ge=0, description="Total investments")
    net_worth: float = Field(0, description="Net worth (can be negative)")

    class Config:
        schema_extra = {
            "example": {
                "year": 2024,
                "month": 1,
                "total_income": 5000,
                "total_expenses": 3000,
                "total_savings": 1500,
                "total_investments": 500,
                "net_worth": 50000
            }
        }


class FinancialSummaryResponse(BaseModel):
    """Response schema for financial summary."""
    id: UUID
    user_id: UUID
    year: int
    month: int
    total_income: float
    total_expenses: float
    total_savings: float
    total_investments: float
    net_worth: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================

class TransactionCreate(BaseModel):
    """Request schema for creating a transaction."""
    transaction_date: date = Field(..., description="Transaction date")
    amount: float = Field(..., gt=0, description="Transaction amount (positive)")
    category: str = Field(..., min_length=1, max_length=50, description="Category")
    merchant_name: Optional[str] = Field(None, max_length=255, description="Merchant name")
    transaction_type: Optional[str] = Field(None, pattern=r"^(INCOME|EXPENSE|INVESTMENT)?$", description="Type")
    payment_method: Optional[str] = Field(None, pattern=r"^(CARD|BANK_TRANSFER|CASH|CHECK)?$", description="Payment method")
    description: Optional[str] = Field(None, description="Description")
    is_recurring: bool = Field(False, description="Is recurring transaction")

    class Config:
        schema_extra = {
            "example": {
                "transaction_date": "2024-01-15",
                "amount": 150.00,
                "category": "Groceries",
                "merchant_name": "Whole Foods",
                "transaction_type": "EXPENSE",
                "payment_method": "CARD",
                "is_recurring": False
            }
        }


class TransactionResponse(BaseModel):
    """Response schema for transaction."""
    id: UUID
    user_id: UUID
    transaction_date: date
    amount: float
    category: str
    merchant_name: Optional[str]
    transaction_type: Optional[str]
    payment_method: Optional[str]
    description: Optional[str]
    is_recurring: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""
    items: List[TransactionResponse]
    total: int
    skip: int
    limit: int

    class Config:
        schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "skip": 0,
                "limit": 20
            }
        }


# ============================================================================
# GOAL SCHEMAS
# ============================================================================

class GoalCreate(BaseModel):
    """Request schema for creating a financial goal."""
    goal_name: str = Field(..., min_length=1, max_length=255, description="Goal name")
    description: Optional[str] = Field(None, description="Goal description")
    target_amount: float = Field(..., gt=0, description="Target amount (positive)")
    current_amount: float = Field(0, ge=0, description="Current amount (non-negative)")
    target_date: Optional[date] = Field(None, description="Target achievement date")
    goal_type: Optional[str] = Field(None, description="Goal type")
    status: str = Field("ACTIVE", pattern=r"^(ACTIVE|COMPLETED|ABANDONED)$", description="Status")
    priority: Optional[str] = Field(None, pattern=r"^(LOW|MEDIUM|HIGH)?$", description="Priority")

    class Config:
        schema_extra = {
            "example": {
                "goal_name": "Buy a house",
                "description": "Save for down payment",
                "target_amount": 50000,
                "current_amount": 15000,
                "target_date": "2025-12-31",
                "goal_type": "SAVINGS",
                "status": "ACTIVE",
                "priority": "HIGH"
            }
        }


class GoalResponse(BaseModel):
    """Response schema for financial goal."""
    id: UUID
    user_id: UUID
    goal_name: str
    description: Optional[str]
    target_amount: float
    current_amount: float
    target_date: Optional[date]
    goal_type: Optional[str]
    status: str
    priority: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.target_amount == 0:
            return 0.0
        return min(100, (self.current_amount / self.target_amount) * 100)


# ============================================================================
# HOLDING SCHEMAS
# ============================================================================

class HoldingCreate(BaseModel):
    """Request schema for creating a holding."""
    ticker: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    quantity: float = Field(..., gt=0, description="Quantity (positive)")
    average_cost: float = Field(..., gt=0, description="Average cost per unit (positive)")
    current_value: Optional[float] = Field(None, description="Current market value")
    asset_type: Optional[str] = Field(None, description="Asset type")
    purchase_date: Optional[date] = Field(None, description="Purchase date")

    class Config:
        schema_extra = {
            "example": {
                "ticker": "AAPL",
                "quantity": 10.5,
                "average_cost": 150.00,
                "current_value": 1680.50,
                "asset_type": "EQUITY",
                "purchase_date": "2023-06-15"
            }
        }


class HoldingResponse(BaseModel):
    """Response schema for holding."""
    id: UUID
    user_id: UUID
    ticker: str
    quantity: float
    average_cost: float
    current_value: Optional[float]
    asset_type: Optional[str]
    purchase_date: Optional[date]
    last_updated: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# MARKET_PRICE SCHEMAS
# ============================================================================

class MarketPriceCreate(BaseModel):
    """Request schema for creating market price record."""
    ticker: str = Field(..., min_length=1, max_length=20, description="Ticker symbol")
    price_date: date = Field(..., description="Price date")
    open_price: float = Field(..., gt=0, description="Open price (positive)")
    close_price: float = Field(..., gt=0, description="Close price (positive)")
    high_price: float = Field(..., gt=0, description="High price (positive)")
    low_price: float = Field(..., gt=0, description="Low price (positive)")
    volume: Optional[int] = Field(None, ge=0, description="Trading volume")

    @validator('high_price')
    def validate_high(cls, v, values):
        """Ensure high >= low."""
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('high_price must be >= low_price')
        return v

    class Config:
        schema_extra = {
            "example": {
                "ticker": "AAPL",
                "price_date": "2024-01-15",
                "open_price": 180.00,
                "close_price": 185.50,
                "high_price": 186.00,
                "low_price": 179.50,
                "volume": 50000000
            }
        }


class MarketPriceResponse(BaseModel):
    """Response schema for market price."""
    id: UUID
    ticker: str
    price_date: date
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    volume: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# CONSENT_LOG SCHEMAS
# ============================================================================

class ConsentLogCreate(BaseModel):
    """Request schema for creating consent record."""
    consent_type: str = Field(..., min_length=1, max_length=100, description="Consent type")
    granted: bool = Field(False, description="Consent granted")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        schema_extra = {
            "example": {
                "consent_type": "MARKETING_EMAILS",
                "granted": True,
                "notes": "User opted in"
            }
        }


class ConsentLogResponse(BaseModel):
    """Response schema for consent log."""
    id: UUID
    user_id: UUID
    consent_type: str
    granted: bool
    timestamp: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# AUDIT_LOG SCHEMAS
# ============================================================================

class AuditLogCreate(BaseModel):
    """Request schema for creating audit log."""
    action: str = Field(..., min_length=1, max_length=100, description="Action")
    resource_type: str = Field(..., min_length=1, max_length=50, description="Resource type")
    resource_id: Optional[str] = Field(None, max_length=100, description="Resource ID")
    details: Optional[dict] = Field(None, description="Additional details")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")

    class Config:
        schema_extra = {
            "example": {
                "action": "USER_LOGIN",
                "resource_type": "USER",
                "resource_id": "123e4567-e89b-12d3-a456-426614174000",
                "details": {"method": "password"},
                "ip_address": "192.168.1.1"
            }
        }


class AuditLogResponse(BaseModel):
    """Response schema for audit log."""
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[dict]
    timestamp: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# FINANCIAL REPORT SCHEMAS
# ============================================================================

class FinancialReportRequest(BaseModel):
    """Request schema for financial report generation."""
    period: Optional[str] = Field("current", description="Period (current, last_month, last_3_months, last_year)")

    class Config:
        schema_extra = {
            "example": {
                "period": "current"
            }
        }


class GoalSummary(BaseModel):
    """Summary information for a single goal."""
    goal_id: UUID
    goal_name: str
    target_amount: float
    current_amount: float
    progress_percentage: float
    status: str

    class Config:
        schema_extra = {
            "example": {
                "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                "goal_name": "Emergency Fund",
                "target_amount": 10000,
                "current_amount": 5500,
                "progress_percentage": 55.0,
                "status": "ACTIVE"
            }
        }


class PortfolioSummary(BaseModel):
    """Summary information for investment holdings."""
    total_value: float
    total_cost_basis: float
    unrealized_gain_loss: float
    gain_loss_percentage: float
    holdings_count: int

    class Config:
        schema_extra = {
            "example": {
                "total_value": 50000,
                "total_cost_basis": 45000,
                "unrealized_gain_loss": 5000,
                "gain_loss_percentage": 11.11,
                "holdings_count": 15
            }
        }


class FinancialReportResponse(BaseModel):
    """Response schema for financial report."""
    user_id: UUID
    report_date: datetime
    period: str
    total_income: float
    total_expenses: float
    savings_amount: float
    savings_rate: float
    net_worth: float
    investment_value: float
    goals_summary: List[GoalSummary]
    portfolio_summary: Optional[PortfolioSummary]

    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "report_date": "2024-01-15T12:00:00",
                "period": "current",
                "total_income": 5000,
                "total_expenses": 3000,
                "savings_amount": 2000,
                "savings_rate": 40.0,
                "net_worth": 100000,
                "investment_value": 50000,
                "goals_summary": [],
                "portfolio_summary": None
            }
        }


# ============================================================================
# AI ADVICE SCHEMAS
# ============================================================================

class AIAdviceRequest(BaseModel):
    """Request schema for AI advice generation."""
    question: Optional[str] = Field(None, description="Specific question for AI")
    include_report: bool = Field(True, description="Include financial report in context")

    class Config:
        schema_extra = {
            "example": {
                "question": "How can I improve my savings rate?",
                "include_report": True
            }
        }


class AIAdviceResponse(BaseModel):
    """Response schema for AI advice."""
    user_id: UUID
    advice: str
    confidence: float = Field(0.85, ge=0, le=1, description="Confidence score")
    generated_at: datetime
    source: str = Field("local", description="Advice source (local or gemini)")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "advice": "Based on your financial data, consider increasing your investment allocation...",
                "confidence": 0.85,
                "generated_at": "2024-01-15T12:00:00",
                "source": "local"
            }
        }


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    detail: Optional[str] = None
    status_code: int

    class Config:
        schema_extra = {
            "example": {
                "error": "Not Found",
                "detail": "User with ID '123' not found",
                "status_code": 404
            }
        }


# Update forward references for nested models
UserDetailResponse.update_forward_refs()
