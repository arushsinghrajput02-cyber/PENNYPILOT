from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import SavingsGoal, GoalContribution, User, Transaction
from backend.schemas import (
    SavingsGoalCreate,
    SavingsGoalUpdate,
    SavingsGoalOut,
    GoalContributionCreate,
    GoalContributionOut
)
from backend.security import get_current_user

router = APIRouter(prefix="/goals", tags=["Savings Goals"])


def format_goal_out(goal: SavingsGoal) -> SavingsGoalOut:
    """Helper to calculate percentage complete, remaining amount, and days remaining."""
    target = float(goal.target_amount)
    current = float(goal.current_amount)
    remaining = max(0.0, target - current)
    pct = round(min(100.0, (current / target * 100.0)), 1) if target > 0 else 0.0

    today = date.today()
    days_left = (goal.target_date - today).days

    contributions_out = [
        GoalContributionOut.model_validate(c) for c in goal.contributions
    ]

    return SavingsGoalOut(
        id=goal.id,
        user_id=goal.user_id,
        title=goal.title,
        target_amount=target,
        current_amount=current,
        remaining_amount=remaining,
        percentage_complete=pct,
        target_date=goal.target_date,
        days_remaining=days_left,
        category=goal.category,
        status="completed" if current >= target else goal.status,
        created_at=goal.created_at,
        contributions=contributions_out
    )


@router.get("", response_model=List[SavingsGoalOut])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all savings goals for the authenticated student."""
    goals = (
        db.query(SavingsGoal)
        .filter(SavingsGoal.user_id == current_user.id)
        .order_by(desc(SavingsGoal.created_at))
        .all()
    )
    return [format_goal_out(g) for g in goals]


@router.post("", response_model=SavingsGoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_in: SavingsGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new savings goal with optional initial deposit."""
    initial_deposit = max(0.0, goal_in.initial_deposit or 0.0)
    goal = SavingsGoal(
        user_id=current_user.id,
        title=goal_in.title.strip(),
        target_amount=round(float(goal_in.target_amount), 2),
        current_amount=round(initial_deposit, 2),
        target_date=goal_in.target_date,
        category=goal_in.category or "General",
        status="completed" if initial_deposit >= goal_in.target_amount else "active"
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    if initial_deposit > 0:
        contribution = GoalContribution(
            goal_id=goal.id,
            user_id=current_user.id,
            amount=initial_deposit,
            note="Initial deposit",
            contribution_date=date.today()
        )
        db.add(contribution)
        db.commit()
        db.refresh(goal)

    return format_goal_out(goal)


@router.get("/{goal_id}", response_model=SavingsGoalOut)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve a single savings goal."""
    goal = db.query(SavingsGoal).filter(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return format_goal_out(goal)


@router.put("/{goal_id}", response_model=SavingsGoalOut)
def update_goal(
    goal_id: int,
    goal_in: SavingsGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update goal settings."""
    goal = db.query(SavingsGoal).filter(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    if goal_in.title is not None:
        goal.title = goal_in.title.strip()
    if goal_in.target_amount is not None:
        goal.target_amount = round(float(goal_in.target_amount), 2)
    if goal_in.target_date is not None:
        goal.target_date = goal_in.target_date
    if goal_in.category is not None:
        goal.category = goal_in.category.strip()
    if goal_in.status is not None:
        goal.status = goal_in.status

    db.commit()
    db.refresh(goal)
    return format_goal_out(goal)


@router.post("/{goal_id}/contribute", response_model=SavingsGoalOut)
def contribute_to_goal(
    goal_id: int,
    contrib_in: GoalContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a deposit/contribution to a savings goal."""
    goal = db.query(SavingsGoal).filter(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    amount = round(float(contrib_in.amount), 2)
    goal.current_amount += amount
    if goal.current_amount >= goal.target_amount:
        goal.status = "completed"

    contrib_date = contrib_in.contribution_date or date.today()
    contribution = GoalContribution(
        goal_id=goal.id,
        user_id=current_user.id,
        amount=amount,
        note=contrib_in.note.strip() if contrib_in.note else "Savings deposit",
        contribution_date=contrib_date
    )
    db.add(contribution)

    # Also log a corresponding transaction with need_or_want="saving"
    tx = Transaction(
        user_id=current_user.id,
        amount=amount,
        transaction_type="expense",
        category="Savings & Investments",
        description=f"Deposit into goal: {goal.title}",
        transaction_date=contrib_date,
        need_or_want="saving"
    )
    db.add(tx)

    db.commit()
    db.refresh(goal)
    return format_goal_out(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a savings goal."""
    goal = db.query(SavingsGoal).filter(SavingsGoal.id == goal_id, SavingsGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    db.delete(goal)
    db.commit()
    return None
