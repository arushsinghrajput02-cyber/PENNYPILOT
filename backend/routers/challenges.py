from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database import get_db
from backend.models import Challenge, Transaction, User
from backend.schemas import ChallengeCreate, ChallengeOut
from backend.security import get_current_user

router = APIRouter(prefix="/challenges", tags=["Challenges"])


def evaluate_challenge(challenge: Challenge, db: Session) -> ChallengeOut:
    """Calculate live spending during challenge dates and determine on-track status."""
    today = date.today()

    query = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == challenge.user_id,
            Transaction.transaction_type == "expense",
            Transaction.transaction_date >= challenge.start_date,
            Transaction.transaction_date <= challenge.end_date
        )
    )

    if challenge.category == "All Non-Essentials":
        query = query.filter(Transaction.need_or_want == "want")
    elif challenge.category != "Overall":
        query = query.filter(Transaction.category == challenge.category)

    current_spent = float(query.scalar() or 0.0)
    is_on_track = current_spent <= challenge.target_amount

    # Auto-resolve status if past end date
    current_status = challenge.status
    if current_status == "active" and today > challenge.end_date:
        current_status = "completed" if is_on_track else "failed"
        challenge.status = current_status
        db.commit()

    days_left = max(0, (challenge.end_date - today).days)

    return ChallengeOut(
        id=challenge.id,
        user_id=challenge.user_id,
        title=challenge.title,
        description=challenge.description,
        category=challenge.category,
        target_amount=challenge.target_amount,
        current_spent=round(current_spent, 2),
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        days_left=days_left,
        status=current_status,
        is_on_track=is_on_track,
        created_at=challenge.created_at
    )


@router.get("", response_model=List[ChallengeOut])
def get_challenges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all challenges for the current user."""
    challenges = (
        db.query(Challenge)
        .filter(Challenge.user_id == current_user.id)
        .order_by(desc(Challenge.created_at))
        .all()
    )
    return [evaluate_challenge(c, db) for c in challenges]


@router.post("", response_model=ChallengeOut, status_code=status.HTTP_201_CREATED)
def create_challenge(
    c_in: ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new no-spend or budget challenge."""
    new_challenge = Challenge(
        user_id=current_user.id,
        title=c_in.title.strip(),
        description=c_in.description.strip() if c_in.description else "",
        category=c_in.category.strip(),
        target_amount=round(float(c_in.target_amount), 2),
        start_date=c_in.start_date,
        end_date=c_in.end_date,
        status="active"
    )
    db.add(new_challenge)
    db.commit()
    db.refresh(new_challenge)
    return evaluate_challenge(new_challenge, db)


@router.delete("/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a challenge."""
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id, Challenge.user_id == current_user.id).first()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    db.delete(challenge)
    db.commit()
    return None
