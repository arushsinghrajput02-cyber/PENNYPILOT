import calendar
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc

from backend.database import get_db
from backend.models import Transaction, Budget, User
from backend.schemas import (
    DashboardSummary,
    CategoryBreakdownItem,
    MonthlyTrendItem,
    NeedsWantsSummary,
    SurvivalModeResponse,
    ForecastResponse,
    FinancialHealthScoreResponse,
    SmartInsight,
    TransactionOut
)
from backend.security import get_current_user
from backend.services.insights import generate_smart_insights
from backend.services.forecasting import calculate_month_end_forecast
from backend.services.financial_score import calculate_financial_health_score

router = APIRouter(prefix="/analytics", tags=["Analytics & Insights"])


@router.get("/overview", response_model=DashboardSummary)
def get_dashboard_summary(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve top-level KPI metrics for the student dashboard."""
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    # All-time totals
    all_income = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == current_user.id, Transaction.transaction_type == "income")
        .scalar() or 0.0
    )
    all_expense = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == current_user.id, Transaction.transaction_type == "expense")
        .scalar() or 0.0
    )
    all_income = float(all_income)
    all_expense = float(all_expense)
    current_balance = round(all_income - all_expense, 2)

    # Monthly totals
    monthly_inc = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "income",
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        )
        .scalar() or 0.0
    )
    monthly_exp = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        )
        .scalar() or 0.0
    )
    monthly_inc = float(monthly_inc)
    monthly_exp = float(monthly_exp)
    monthly_savings = round(monthly_inc - monthly_exp, 2)

    savings_rate = round(max(0.0, (monthly_savings / monthly_inc * 100.0)), 1) if monthly_inc > 0 else 0.0

    # Monthly budget
    budget_row = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.month == target_month,
            Budget.year == target_year,
            Budget.category == "Overall"
        )
        .first()
    )
    if budget_row:
        total_b = float(budget_row.monthly_limit)
    else:
        # Sum category budgets
        cat_budgets = (
            db.query(func.sum(Budget.monthly_limit))
            .filter(
                Budget.user_id == current_user.id,
                Budget.month == target_month,
                Budget.year == target_year,
                Budget.category != "Overall"
            )
            .scalar() or 0.0
        )
        total_b = float(cat_budgets)

    budget_util = round((monthly_exp / total_b * 100.0), 1) if total_b > 0 else 0.0

    return DashboardSummary(
        current_balance=current_balance,
        total_income_all_time=round(all_income, 2),
        total_expense_all_time=round(all_expense, 2),
        monthly_income=round(monthly_inc, 2),
        monthly_expenses=round(monthly_exp, 2),
        monthly_savings=monthly_savings,
        savings_rate=savings_rate,
        budget_utilization=budget_util,
        total_budget=round(total_b, 2),
        currency_symbol="₹",
        month=target_month,
        year=target_year
    )


@router.get("/category-breakdown", response_model=List[CategoryBreakdownItem])
def get_category_breakdown(
    transaction_type: str = Query("expense", pattern="^(income|expense)$"),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve category breakdown for pie and doughnut chart visualisations."""
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    query = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == transaction_type,
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        )
        .group_by(Transaction.category)
        .order_by(desc("total"))
    )

    rows = query.all()
    total_amount = sum(float(r.total) for r in rows)

    results = []
    for r in rows:
        amt = float(r.total)
        pct = round((amt / total_amount * 100.0), 1) if total_amount > 0 else 0.0
        results.append(CategoryBreakdownItem(
            category=r.category,
            amount=round(amt, 2),
            percentage=pct,
            count=int(r.count),
            transaction_type=transaction_type
        ))

    return results


@router.get("/monthly-trend", response_model=List[MonthlyTrendItem])
def get_monthly_trend(
    months_count: int = Query(6, ge=2, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve past N months of income, expense, and savings trends for line and bar charts."""
    today = date.today()
    results = []

    for i in range(months_count - 1, -1, -1):
        # Calculate year and month for step
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1

        inc = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "income",
                extract("month", Transaction.transaction_date) == m,
                extract("year", Transaction.transaction_date) == y
            )
            .scalar() or 0.0
        )
        exp = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "expense",
                extract("month", Transaction.transaction_date) == m,
                extract("year", Transaction.transaction_date) == y
            )
            .scalar() or 0.0
        )

        inc = float(inc)
        exp = float(exp)
        month_label = f"{calendar.month_abbr[m]} {y}"
        month_key = f"{y:04d}-{m:02d}"

        results.append(MonthlyTrendItem(
            month_key=month_key,
            month_name=month_label,
            income=round(inc, 2),
            expenses=round(exp, 2),
            savings=round(inc - exp, 2)
        ))

    return results


@router.get("/needs-wants", response_model=NeedsWantsSummary)
def get_needs_vs_wants(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Feature 3: Needs vs Wants vs Savings proportional breakdown."""
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    rows = (
        db.query(
            Transaction.need_or_want,
            func.sum(Transaction.amount).label("total")
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        )
        .group_by(Transaction.need_or_want)
        .all()
    )

    data = {r.need_or_want: float(r.total) for r in rows}
    needs_amt = data.get("need", 0.0)
    wants_amt = data.get("want", 0.0)
    savings_amt = data.get("saving", 0.0)
    total_exp = needs_amt + wants_amt + savings_amt

    n_pct = round((needs_amt / total_exp * 100.0), 1) if total_exp > 0 else 0.0
    w_pct = round((wants_amt / total_exp * 100.0), 1) if total_exp > 0 else 0.0
    s_pct = round((savings_amt / total_exp * 100.0), 1) if total_exp > 0 else 0.0

    return NeedsWantsSummary(
        needs_amount=round(needs_amt, 2),
        needs_percentage=n_pct,
        wants_amount=round(wants_amt, 2),
        wants_percentage=w_pct,
        savings_amount=round(savings_amt, 2),
        savings_percentage=s_pct,
        total_spending=round(total_exp, 2)
    )


@router.get("/survival-mode", response_model=SurvivalModeResponse)
def get_survival_mode(
    reserve: Optional[float] = Query(None, ge=0.0),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Feature 2: Survival Mode Daily Limit Engine.
    Suggested daily limit = (Current Balance - Reserved Buffer) / Remaining Days in Month.
    """
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    # All-time available balance
    all_income = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == current_user.id, Transaction.transaction_type == "income")
        .scalar() or 0.0
    )
    all_expense = (
        db.query(func.sum(Transaction.amount))
        .filter(Transaction.user_id == current_user.id, Transaction.transaction_type == "expense")
        .scalar() or 0.0
    )
    current_balance = float(all_income) - float(all_expense)

    # User configured or query overridden reserve buffer
    reserved_buffer = reserve if reserve is not None else float(current_user.monthly_reserved_amount or 0.0)
    spendable = current_balance - reserved_buffer

    # Days remaining in current month
    _, total_days = calendar.monthrange(target_year, target_month)
    if target_month == today.month and target_year == today.year:
        days_remaining = max(1, total_days - today.day + 1)
    else:
        days_remaining = total_days

    daily_limit = round(spendable / float(days_remaining), 2) if spendable > 0 else 0.0

    if spendable <= 0:
        status_mode = "depleted"
        message = "Survival Alert: Spendable balance depleted or fully reserved. Restrict all non-essential outflows."
    elif daily_limit < 100.0:
        status_mode = "critical"
        message = f"Strict Survival Mode: Suggested cap is ₹{daily_limit:,.0f}/day to survive the next {days_remaining} days."
    elif daily_limit < 300.0:
        status_mode = "caution"
        message = f"Moderate Survival Mode: Keep discretionary spending under ₹{daily_limit:,.0f}/day."
    else:
        status_mode = "safe"
        message = f"Healthy Balance: You have a comfortable daily spending allowance of ₹{daily_limit:,.0f}/day."

    explanation = (
        f"Available net balance (₹{current_balance:,.0f}) minus reserved funds (₹{reserved_buffer:,.0f}) "
        f"leaves ₹{max(0.0, spendable):,.0f} spendable across {days_remaining} days remaining in {calendar.month_name[target_month]}."
    )

    return SurvivalModeResponse(
        current_balance=round(current_balance, 2),
        reserved_amount=round(reserved_buffer, 2),
        spendable_balance=round(spendable, 2),
        days_remaining_in_month=days_remaining,
        suggested_daily_limit=daily_limit,
        status=status_mode,
        message=message,
        explanation=explanation
    )


@router.get("/forecast", response_model=ForecastResponse)
def get_month_end_forecast(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Feature 5: Transparent Month-End Spending Forecast."""
    today = date.today()
    target_date = date(year or today.year, month or today.month, 1 if month != today.month else today.day)
    return calculate_month_end_forecast(current_user.id, db, target_date=target_date)


@router.get("/financial-score", response_model=FinancialHealthScoreResponse)
def get_financial_score(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Feature 6: Objective 0-100 Financial Health Score."""
    today = date.today()
    target_date = date(year or today.year, month or today.month, 1 if month != today.month else today.day)
    return calculate_financial_health_score(current_user.id, db, target_date=target_date)


@router.get("/insights", response_model=List[SmartInsight])
def get_smart_coach_insights(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Feature 1: Smart Spend Coach Rule-Based Insights Engine."""
    today = date.today()
    target_date = date(year or today.year, month or today.month, 1 if month != today.month else today.day)
    raw_insights = generate_smart_insights(current_user.id, db, target_date=target_date)
    return [SmartInsight(**item) for item in raw_insights]


@router.get("/recurring", response_model=List[TransactionOut])
def get_recurring_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve recurring student expense commitments (hostel, mess, wifi, subscriptions)."""
    items = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            Transaction.is_recurring == True
        )
        .order_by(desc(Transaction.transaction_date))
        .all()
    )
    return [TransactionOut.model_validate(t) for t in items]
