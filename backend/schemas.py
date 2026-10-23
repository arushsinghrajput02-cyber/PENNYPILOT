from datetime import date, datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# ================= USER SCHEMAS =================

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    monthly_reserved_amount: Optional[float] = Field(None, ge=0.0)


class UserOut(UserBase):
    id: int
    monthly_reserved_amount: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ================= TRANSACTION SCHEMAS =================

class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    transaction_type: Literal["income", "expense"]
    category: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    transaction_date: date = Field(default_factory=date.today)
    need_or_want: Literal["need", "want", "saving"] = "need"
    is_recurring: bool = False


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    transaction_type: Optional[Literal["income", "expense"]] = None
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    transaction_date: Optional[date] = None
    need_or_want: Optional[Literal["need", "want", "saving"]] = None
    is_recurring: Optional[bool] = None


class TransactionOut(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: List[TransactionOut]
    total: int
    page: int
    limit: int
    total_pages: int


# ================= BUDGET SCHEMAS =================

class BudgetCreate(BaseModel):
    category: str = Field(..., min_length=2, max_length=100)
    monthly_limit: float = Field(..., gt=0)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)


class BudgetUpdate(BaseModel):
    monthly_limit: float = Field(..., gt=0)


class BudgetOut(BaseModel):
    id: int
    user_id: int
    category: str
    monthly_limit: float
    month: int
    year: int
    created_at: datetime
    spent_amount: float = 0.0
    remaining_amount: float = 0.0
    percentage_used: float = 0.0
    status: Literal["normal", "warning", "exceeded"] = "normal"

    model_config = ConfigDict(from_attributes=True)


class BudgetSummaryResponse(BaseModel):
    month: int
    year: int
    total_budget: float
    total_spent: float
    overall_percentage: float
    status: str
    items: List[BudgetOut]


# ================= SAVINGS GOALS SCHEMAS =================

class GoalContributionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    note: Optional[str] = Field(None, max_length=255)
    contribution_date: Optional[date] = Field(default_factory=date.today)


class GoalContributionOut(BaseModel):
    id: int
    goal_id: int
    amount: float
    note: Optional[str]
    contribution_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavingsGoalCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    target_amount: float = Field(..., gt=0)
    target_date: date
    category: Optional[str] = "General"
    initial_deposit: Optional[float] = Field(0.0, ge=0)

    @field_validator("target_date")
    def target_date_must_be_future_or_today(cls, v):
        if v < date.today():
            raise ValueError("Target date cannot be in the past")
        return v


class SavingsGoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    category: Optional[str] = None
    status: Optional[Literal["active", "completed", "paused"]] = None


class SavingsGoalOut(BaseModel):
    id: int
    user_id: int
    title: str
    target_amount: float
    current_amount: float
    remaining_amount: float
    percentage_complete: float
    target_date: date
    days_remaining: int
    category: str
    status: str
    created_at: datetime
    contributions: List[GoalContributionOut] = []

    model_config = ConfigDict(from_attributes=True)


# ================= CHALLENGES SCHEMAS =================

class ChallengeCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    category: str = Field("All Non-Essentials", min_length=2, max_length=100)
    target_amount: float = Field(0.0, ge=0.0, description="Max allowed spending during challenge")
    start_date: date
    end_date: date

    @field_validator("end_date")
    def validate_dates(cls, v, info):
        start_date = info.data.get("start_date")
        if start_date and v < start_date:
            raise ValueError("End date must be on or after start date")
        return v


class ChallengeOut(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    category: str
    target_amount: float
    current_spent: float
    start_date: date
    end_date: date
    days_left: int
    status: Literal["active", "completed", "failed"]
    is_on_track: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ================= ANALYTICS SCHEMAS =================

class DashboardSummary(BaseModel):
    current_balance: float
    total_income_all_time: float
    total_expense_all_time: float
    monthly_income: float
    monthly_expenses: float
    monthly_savings: float
    savings_rate: float
    budget_utilization: float
    total_budget: float
    currency_symbol: str = "₹"
    month: int
    year: int


class CategoryBreakdownItem(BaseModel):
    category: str
    amount: float
    percentage: float
    count: int
    transaction_type: str


class MonthlyTrendItem(BaseModel):
    month_key: str  # YYYY-MM
    month_name: str  # Oct 2026
    income: float
    expenses: float
    savings: float


class NeedsWantsSummary(BaseModel):
    needs_amount: float
    needs_percentage: float
    wants_amount: float
    wants_percentage: float
    savings_amount: float
    savings_percentage: float
    total_spending: float


class SurvivalModeResponse(BaseModel):
    current_balance: float
    reserved_amount: float
    spendable_balance: float
    days_remaining_in_month: int
    suggested_daily_limit: float
    status: Literal["safe", "caution", "critical", "depleted"]
    message: str
    explanation: str


class ForecastResponse(BaseModel):
    projected_end_of_month_spend: float
    current_spent_this_month: float
    average_daily_burn: float
    days_elapsed: int
    days_remaining: int
    total_days_in_month: int
    is_sufficient_data: bool
    confidence_note: str


class FinancialHealthScoreResponse(BaseModel):
    overall_score: int  # 0 to 100
    rating: str  # "Excellent", "Good", "Fair", "Needs Attention"
    factors: dict
    insights: List[str]


class SmartInsight(BaseModel):
    id: str
    type: Literal["warning", "positive", "tip", "alert"]
    title: str
    message: str
    impact: Optional[str] = None
    category: Optional[str] = None
