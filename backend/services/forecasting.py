import calendar
from datetime import date
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from backend.models import Transaction


def calculate_month_end_forecast(user_id: int, db: Session, target_date: date = None) -> Dict[str, Any]:
    """
    Compute a transparent month-end spending forecast based on current month run-rate.
    Avoids opaque black-box machine learning; provides fully transparent arithmetic and caveats.
    """
    if target_date is None:
        target_date = date.today()

    current_year = target_date.year
    current_month = target_date.month
    current_day = target_date.day

    # Number of days in current month
    _, total_days_in_month = calendar.monthrange(current_year, current_month)
    days_elapsed = max(current_day, 1)
    days_remaining = max(total_days_in_month - current_day, 0)

    # Total expenses recorded so far in current month
    current_spent = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == current_month,
            extract("year", Transaction.transaction_date) == current_year
        )
        .scalar() or 0.0
    )
    current_spent = float(current_spent)

    if current_spent <= 0:
        return {
            "projected_end_of_month_spend": 0.0,
            "current_spent_this_month": 0.0,
            "average_daily_burn": 0.0,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "total_days_in_month": total_days_in_month,
            "is_sufficient_data": False,
            "confidence_note": "No expenses recorded this month yet to build a forecast projection."
        }

    # Daily burn rate based on days elapsed
    average_daily_burn = current_spent / float(days_elapsed)
    projected_total = round(average_daily_burn * float(total_days_in_month), 2)

    # Transparency notes depending on how far along we are in the month
    if days_elapsed < 4:
        is_sufficient = False
        confidence_note = (
            f"Preliminary estimate based on early data ({days_elapsed} of {total_days_in_month} days). "
            f"Run-rate will stabilize as more transactions are recorded."
        )
    elif days_elapsed < 15:
        is_sufficient = True
        confidence_note = (
            f"Moderate confidence pace projection based on {days_elapsed} days of recorded spending "
            f"(averaging ₹{average_daily_burn:,.1f}/day)."
        )
    else:
        is_sufficient = True
        confidence_note = (
            f"High confidence forecast based on {days_elapsed} days of consistent spending patterns "
            f"in {calendar.month_name[current_month]}."
        )

    return {
        "projected_end_of_month_spend": projected_total,
        "current_spent_this_month": round(current_spent, 2),
        "average_daily_burn": round(average_daily_burn, 2),
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "total_days_in_month": total_days_in_month,
        "is_sufficient_data": is_sufficient,
        "confidence_note": confidence_note
    }
