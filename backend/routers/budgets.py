from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from backend.database import get_db
from backend.models import Budget, Transaction, User
from backend.schemas import BudgetCreate, BudgetUpdate, BudgetOut, BudgetSummaryResponse
from backend.security import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def compute_budget_status(limit: float, spent: float) -> tuple[float, float, str]:
    """Compute percentage used, remaining amount, and alert status."""
    pct = round((spent / limit * 100.0), 1) if limit > 0 else 0.0
    rem = round(limit - spent, 2)
    if pct >= 100.0:
        st = "exceeded"
    elif pct >= 80.0:
        st = "warning"
    else:
        st = "normal"
    return pct, rem, st


@router.get("", response_model=List[BudgetOut])
def get_budgets(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all budget configurations for a specific month and year with live spending calculations."""
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.month == target_month,
            Budget.year == target_year
        )
        .all()
    )

    # Get actual spending by category for this period
    expense_rows = (
        db.query(
            Transaction.category,
            func.sum(Transaction.amount).label("spent")
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        )
        .group_by(Transaction.category)
        .all()
    )
    spent_map = {row.category: float(row.spent) for row in expense_rows}
    total_spent_month = sum(spent_map.values())

    results = []
    for b in budgets:
        if b.category == "Overall":
            spent = total_spent_month
        else:
            spent = spent_map.get(b.category, 0.0)

        pct, rem, st = compute_budget_status(b.monthly_limit, spent)
        results.append(BudgetOut(
            id=b.id,
            user_id=b.user_id,
            category=b.category,
            monthly_limit=b.monthly_limit,
            month=b.month,
            year=b.year,
            created_at=b.created_at,
            spent_amount=round(spent, 2),
            remaining_amount=rem,
            percentage_used=pct,
            status=st
        ))

    return results


@router.get("/summary", response_model=BudgetSummaryResponse)
def get_budget_summary(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve aggregate budget utilization overview and comparison."""
    today = date.today()
    target_month = month or today.month
    target_year = year or today.year

    # Check for overall budget
    overall_budget = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.month == target_month,
            Budget.year == target_year,
            Budget.category == "Overall"
        )
        .first()
    )

    # All budgets
    budget_items = get_budgets(month=target_month, year=target_year, db=db, current_user=current_user)

    # Actual total monthly spending
    total_spent = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.transaction_type == "expense",
            extract("month", Transaction.transaction_date) == target_month,
            extract("year", Transaction.transaction_date) == target_year
        )
        .scalar() or 0.0
    )
    total_spent = float(total_spent)

    if overall_budget:
        total_limit = overall_budget.monthly_limit
    else:
        # Sum of specific category budgets if no overall budget
        category_limits = [b.monthly_limit for b in budget_items if b.category != "Overall"]
        total_limit = sum(category_limits) if category_limits else 0.0

    overall_pct = round((total_spent / total_limit * 100.0), 1) if total_limit > 0 else 0.0
    if overall_pct >= 100.0:
        summary_status = "exceeded"
    elif overall_pct >= 80.0:
        summary_status = "warning"
    else:
        summary_status = "normal"

    return BudgetSummaryResponse(
        month=target_month,
        year=target_year,
        total_budget=round(total_limit, 2),
        total_spent=round(total_spent, 2),
        overall_percentage=overall_pct,
        status=summary_status,
        items=budget_items
    )


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_or_update_budget(
    b_in: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set or update a budget for a category in a given month/year."""
    existing = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.category == b_in.category.strip(),
            Budget.month == b_in.month,
            Budget.year == b_in.year
        )
        .first()
    )

    if existing:
        existing.monthly_limit = round(float(b_in.monthly_limit), 2)
        db.commit()
        db.refresh(existing)
        target_budget = existing
    else:
        new_b = Budget(
            user_id=current_user.id,
            category=b_in.category.strip(),
            monthly_limit=round(float(b_in.monthly_limit), 2),
            month=b_in.month,
            year=b_in.year
        )
        db.add(new_b)
        db.commit()
        db.refresh(new_b)
        target_budget = new_b

    # Calculate spent amount
    if target_budget.category == "Overall":
        spent = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "expense",
                extract("month", Transaction.transaction_date) == target_budget.month,
                extract("year", Transaction.transaction_date) == target_budget.year
            )
            .scalar() or 0.0
        )
    else:
        spent = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == "expense",
                Transaction.category == target_budget.category,
                extract("month", Transaction.transaction_date) == target_budget.month,
                extract("year", Transaction.transaction_date) == target_budget.year
            )
            .scalar() or 0.0
        )

    spent = float(spent)
    pct, rem, st = compute_budget_status(target_budget.monthly_limit, spent)

    return BudgetOut(
        id=target_budget.id,
        user_id=target_budget.user_id,
        category=target_budget.category,
        monthly_limit=target_budget.monthly_limit,
        month=target_budget.month,
        year=target_budget.year,
        created_at=target_budget.created_at,
        spent_amount=round(spent, 2),
        remaining_amount=rem,
        percentage_used=pct,
        status=st
    )


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a budget item."""
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == current_user.id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    db.delete(budget)
    db.commit()
    return None
