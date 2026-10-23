from datetime import date
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from backend.models import Transaction, Budget


def generate_smart_insights(user_id: int, db: Session, target_date: date = None) -> List[Dict[str, Any]]:
    """
    Generate transparent, deterministic, rule-based financial insights based strictly 
    on actual user transactions and budgets. No speculative or false AI claims.
    """
    if target_date is None:
        target_date = date.today()

    current_month = target_date.month
    current_year = target_date.year

    # Calculate previous month and year
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    insights = []

    # 1. Fetch current month expenses by category
    curr_expenses_query = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count(Transaction.id).label("count")
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == current_month,
            extract("year", Transaction.transaction_date) == current_year
        )
        .group_by(Transaction.category)
        .all()
    )

    curr_category_map = {row.category: float(row.total) for row in curr_expenses_query}
    total_curr_expenses = sum(curr_category_map.values())

    # 2. Fetch previous month expenses by category
    prev_expenses_query = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("total")
        )
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == prev_month,
            extract("year", Transaction.transaction_date) == prev_year
        )
        .group_by(Transaction.category)
        .all()
    )
    prev_category_map = {row.category: float(row.total) for row in prev_expenses_query}

    # Rule A: Category Surge Detection (Month-over-Month)
    for cat, curr_amount in curr_category_map.items():
        if cat in prev_category_map and prev_category_map[cat] > 0:
            prev_amount = prev_category_map[cat]
            diff_pct = ((curr_amount - prev_amount) / prev_amount) * 100.0
            if diff_pct >= 20.0 and curr_amount >= 500:
                insights.append({
                    "id": f"surge_{cat.lower().replace(' ', '_')}",
                    "type": "warning",
                    "category": cat,
                    "title": f"Higher Spending in {cat}",
                    "message": f"You have spent {diff_pct:.0f}% more on {cat} (₹{curr_amount:,.0f}) compared to last month (₹{prev_amount:,.0f}).",
                    "impact": f"+₹{curr_amount - prev_amount:,.0f} vs last month"
                })
            elif diff_pct <= -20.0 and prev_amount >= 500:
                insights.append({
                    "id": f"drop_{cat.lower().replace(' ', '_')}",
                    "type": "positive",
                    "category": cat,
                    "title": f"Great Savings in {cat}",
                    "message": f"You've cut down spending in {cat} by {abs(diff_pct):.0f}% compared to last month!",
                    "impact": f"-₹{prev_amount - curr_amount:,.0f} saved"
                })

    # Rule B: Category Budget Near-Cap or Exceeded Warnings
    budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.month == current_month,
            Budget.year == current_year
        )
        .all()
    )

    for b in budgets:
        if b.category == "Overall":
            spent = total_curr_expenses
        else:
            spent = curr_category_map.get(b.category, 0.0)

        utilization = (spent / b.monthly_limit * 100.0) if b.monthly_limit > 0 else 0.0

        if utilization >= 100.0:
            insights.append({
                "id": f"budget_exceeded_{b.id}",
                "type": "alert",
                "category": b.category,
                "title": f"Budget Limit Exceeded: {b.category}",
                "message": f"You have reached {utilization:.0f}% of your monthly limit of ₹{b.monthly_limit:,.0f} (spent ₹{spent:,.0f}).",
                "impact": f"Over limit by ₹{spent - b.monthly_limit:,.0f}"
            })
        elif utilization >= 80.0:
            insights.append({
                "id": f"budget_near_{b.id}",
                "type": "warning",
                "category": b.category,
                "title": f"Budget Warning: {b.category}",
                "message": f"Your {b.category} budget has reached {utilization:.0f}% of its allocated limit.",
                "impact": f"₹{b.monthly_limit - spent:,.0f} remaining for this month"
            })

    # Rule C: Micro-Savings Impact ("Wants" Optimization)
    wants_spending = (
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

    if wants_spending > 500:
        # Suggest realistic daily college micro-savings (e.g., ₹30 - ₹50 per day)
        daily_saving = 40.0
        monthly_saving = daily_saving * 30.0
        insights.append({
            "id": "micro_saving_opportunity",
            "type": "tip",
            "category": "Discretionary Spending",
            "title": "Smart Micro-Saving Tip",
            "message": f"Reducing optional discretionary spending by just ₹{daily_saving:.0f} per day could save approximately ₹{monthly_saving:,.0f} in a 30-day month.",
            "impact": f"₹{monthly_saving:,.0f}/month potential savings"
        })

    # Rule D: High Weekend / Leisure Spend
    food_or_dining = curr_category_map.get("Food & Dining", 0.0)
    if total_curr_expenses > 0 and (food_or_dining / total_curr_expenses) > 0.40:
        insights.append({
            "id": "high_food_ratio",
            "type": "tip",
            "category": "Food & Dining",
            "title": "High Food & Mess Spending Proportion",
            "message": f"Food and dining currently accounts for {((food_or_dining / total_curr_expenses) * 100):.0f}% of your total monthly outflow.",
            "impact": f"₹{food_or_dining:,.0f} out of ₹{total_curr_expenses:,.0f}"
        })

    return insights
