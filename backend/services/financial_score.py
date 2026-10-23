from datetime import date
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from backend.models import Transaction, Budget


def calculate_financial_health_score(user_id: int, db: Session, target_date: date = None) -> Dict[str, Any]:
    """
    Calculate an objective, transparent Financial Health Score (0-100) for college students.
    Breakdown:
      - Budget Adherence (30 pts)
      - Savings Rate (30 pts)
      - Needs vs Wants Balance (20 pts)
      - Emergency Buffer / Survival Health (20 pts)
    """
    if target_date is None:
        target_date = date.today()

    current_month = target_date.month
    current_year = target_date.year

    # 1. Total monthly income
    monthly_income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "income",
            extract("month", Transaction.transaction_date) == current_month,
            extract("year", Transaction.transaction_date) == current_year
        )
        .scalar() or 0.0
    )
    monthly_income = float(monthly_income)

    # 2. Total monthly expenses
    monthly_expenses = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == current_month,
            extract("year", Transaction.transaction_date) == current_year
        )
        .scalar() or 0.0
    )
    monthly_expenses = float(monthly_expenses)

    # 3. Overall cumulative balance (all-time income - all-time expenses)
    all_income = db.query(func.sum(Transaction.amount)).filter(Transaction.user_id == user_id, Transaction.transaction_type == "income").scalar() or 0.0
    all_expense = db.query(func.sum(Transaction.amount)).filter(Transaction.user_id == user_id, Transaction.transaction_type == "expense").scalar() or 0.0
    current_balance = float(all_income) - float(all_expense)

    # If new user or no transactions yet this month:
    if monthly_income == 0 and monthly_expenses == 0:
        return {
            "overall_score": 70,
            "rating": "Neutral Baseline",
            "factors": {
                "budget_adherence": {"score": 20, "max": 30, "detail": "No budget limits breached yet"},
                "savings_rate": {"score": 20, "max": 30, "detail": "Awaiting initial income and expense entries"},
                "needs_vs_wants": {"score": 15, "max": 20, "detail": "Add transactions to calculate ratio"},
                "cash_reserve_buffer": {"score": 15, "max": 20, "detail": "Starting account state"}
            },
            "insights": [
                "Log your first allowance/stipend and expenses to unlock real-time financial health scoring.",
                "Setting category budgets in Budget Planner helps boost your score by up to 30 points."
            ]
        }

    # Factor 1: Budget Adherence (0 - 30 pts)
    budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.month == current_month,
            Budget.year == current_year,
            Budget.category == "Overall"
        )
        .first()
    )

    budget_score = 25  # default if no budget set
    budget_detail = "No overall budget set for this month (default baseline)"

    if budget and budget.monthly_limit > 0:
        utilization = (monthly_expenses / budget.monthly_limit) * 100.0
        if utilization <= 75.0:
            budget_score = 30
            budget_detail = f"Great budget control! Only {utilization:.0f}% utilized"
        elif utilization <= 90.0:
            budget_score = 25
            budget_detail = f"On track: {utilization:.0f}% of budget used"
        elif utilization <= 100.0:
            budget_score = 15
            budget_detail = f"Close to cap: {utilization:.0f}% of budget used"
        else:
            budget_score = max(5, int(30 - (utilization - 100) * 0.5))
            budget_detail = f"Over budget by ₹{monthly_expenses - budget.monthly_limit:,.0f}"

    # Factor 2: Savings Rate (0 - 30 pts)
    savings_score = 15
    savings_rate = 0.0
    if monthly_income > 0:
        net_saved = monthly_income - monthly_expenses
        savings_rate = max(0.0, (net_saved / monthly_income) * 100.0)
        if savings_rate >= 30.0:
            savings_score = 30
            savings_detail = f"Exceptional {savings_rate:.0f}% monthly savings rate"
        elif savings_rate >= 20.0:
            savings_score = 25
            savings_detail = f"Healthy {savings_rate:.0f}% savings rate"
        elif savings_rate >= 10.0:
            savings_score = 18
            savings_detail = f"Moderate {savings_rate:.0f}% savings rate"
        elif savings_rate > 0:
            savings_score = 12
            savings_detail = f"Slim positive savings ({savings_rate:.0f}%)"
        else:
            savings_score = 5
            savings_detail = "Expenses exceed income this month (negative cashflow)"
    else:
        savings_detail = "No income logged this month"
        savings_score = 10 if current_balance > 0 else 5

    # Factor 3: Needs vs Wants Balance (0 - 20 pts)
    # 50/30/20 rule: ideal is Needs around 50%, Wants <= 30%, Savings >= 20%
    wants_amount = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.need_or_want == "want",
            extract("month", Transaction.transaction_date) == current_month,
            extract("year", Transaction.transaction_date) == current_year
        )
        .scalar() or 0.0
    )
    wants_amount = float(wants_amount)

    wants_ratio = (wants_amount / monthly_expenses * 100.0) if monthly_expenses > 0 else 0.0
    if wants_ratio <= 30.0:
        needs_wants_score = 20
        needs_wants_detail = f"Prudent discretionary spending (wants only {wants_ratio:.0f}% of spend)"
    elif wants_ratio <= 45.0:
        needs_wants_score = 15
        needs_wants_detail = f"Acceptable discretionary spending ({wants_ratio:.0f}% on wants)"
    elif wants_ratio <= 60.0:
        needs_wants_score = 10
        needs_wants_detail = f"High discretionary spending ({wants_ratio:.0f}% on wants)"
    else:
        needs_wants_score = 5
        needs_wants_detail = f"Excessive wants spending ({wants_ratio:.0f}% of total outflow)"

    # Factor 4: Cash Reserve Buffer (0 - 20 pts)
    if current_balance >= 10000:
        buffer_score = 20
        buffer_detail = f"Solid cash reserve balance (₹{current_balance:,.0f})"
    elif current_balance >= 4000:
        buffer_score = 16
        buffer_detail = f"Adequate college emergency buffer (₹{current_balance:,.0f})"
    elif current_balance >= 1000:
        buffer_score = 11
        buffer_detail = f"Modest cash cushion remaining (₹{current_balance:,.0f})"
    elif current_balance > 0:
        buffer_score = 6
        buffer_detail = f"Very low liquidity reserve (₹{current_balance:,.0f})"
    else:
        buffer_score = 2
        buffer_detail = "Zero or negative net liquidity balance"

    overall_score = budget_score + savings_score + needs_wants_score + buffer_score
    overall_score = min(max(overall_score, 0), 100)

    if overall_score >= 85:
        rating = "Excellent"
    elif overall_score >= 70:
        rating = "Good"
    elif overall_score >= 50:
        rating = "Fair"
    else:
        rating = "Needs Attention"

    insights: List[str] = []
    if budget_score < 25:
        insights.append("Set or tighten your monthly budget in the Budget Planner to safeguard against overspending.")
    if savings_rate < 20.0 and monthly_income > 0:
        insights.append("Aim to allocate at least 20% of monthly allowance to savings goals.")
    if wants_ratio > 35.0:
        insights.append(f"Discretionary wants make up {wants_ratio:.0f}% of outgoings. Check the 'Needs vs Wants' analytics.")
    if current_balance < 3000:
        insights.append("Survival Mode can help throttle your daily spending until the next stipend or allowance.")
    if not insights:
        insights.append("Great financial discipline! Keep maintaining this saving and budgeting habit.")

    return {
        "overall_score": overall_score,
        "rating": rating,
        "factors": {
            "budget_adherence": {"score": budget_score, "max": 30, "detail": budget_detail},
            "savings_rate": {"score": savings_score, "max": 30, "detail": savings_detail},
            "needs_vs_wants": {"score": needs_wants_score, "max": 20, "detail": needs_wants_detail},
            "cash_reserve_buffer": {"score": buffer_score, "max": 20, "detail": buffer_detail}
        },
        "insights": insights
    }
