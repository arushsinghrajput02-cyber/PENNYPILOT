from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Transaction, Budget, SavingsGoal, GoalContribution, Challenge
from backend.security import hash_password, create_access_token, get_current_user
from backend.schemas import Token, UserOut

router = APIRouter(prefix="/demo", tags=["Demo Mode"])


def populate_student_demo_data(user: User, db: Session):
    """Seed comprehensive, realistic Indian engineering student records for demonstration."""
    today = date.today()
    curr_month = today.month
    curr_year = today.year

    # 1. Clear existing user records to ensure clean state
    db.query(Transaction).filter(Transaction.user_id == user.id).delete()
    db.query(Budget).filter(Budget.user_id == user.id).delete()
    db.query(SavingsGoal).filter(SavingsGoal.user_id == user.id).delete()
    db.query(Challenge).filter(Challenge.user_id == user.id).delete()
    db.commit()

    # 2. Add realistic transactions for Current Month and Last Month
    transactions_data = [
        # --- Current Month Income ---
        {
            "amount": 12000.0,
            "type": "income",
            "category": "Pocket Money / Allowance",
            "description": "Monthly allowance from parents",
            "date": today.replace(day=1),
            "classification": "need",
            "recurring": True
        },
        {
            "amount": 7500.0,
            "type": "income",
            "category": "Part-time / Freelance",
            "description": "FastAPI backend consulting stipend",
            "date": today.replace(day=5),
            "classification": "saving",
            "recurring": False
        },
        {
            "amount": 2500.0,
            "type": "income",
            "category": "Scholarship / Grants",
            "description": "Merit scholarship installment",
            "date": today.replace(day=10),
            "classification": "saving",
            "recurring": False
        },

        # --- Current Month Expenses ---
        {
            "amount": 5500.0,
            "type": "expense",
            "category": "Hostel & Rent",
            "description": "Hostel room rent & electricity",
            "date": today.replace(day=2),
            "classification": "need",
            "recurring": True
        },
        {
            "amount": 1800.0,
            "type": "expense",
            "category": "Food & Dining",
            "description": "Monthly college mess basic card",
            "date": today.replace(day=3),
            "classification": "need",
            "recurring": True
        },
        {
            "amount": 650.0,
            "type": "expense",
            "category": "Books & Academics",
            "description": "Data Structures textbooks & lab manuals",
            "date": today.replace(day=4),
            "classification": "need",
            "recurring": False
        },
        {
            "amount": 420.0,
            "type": "expense",
            "category": "Food & Dining",
            "description": "Campus cafeteria chai and samosa with friends",
            "date": today.replace(day=7),
            "classification": "want",
            "recurring": False
        },
        {
            "amount": 799.0,
            "type": "expense",
            "category": "Transport & Travel",
            "description": "Metro monthly commuter smart card pass",
            "date": today.replace(day=8),
            "classification": "need",
            "recurring": True
        },
        {
            "amount": 1250.0,
            "type": "expense",
            "category": "Tech & Gadgets",
            "description": "USB-C hub & wireless mouse for laptop",
            "date": today.replace(day=12),
            "classification": "want",
            "recurring": False
        },
        {
            "amount": 680.0,
            "type": "expense",
            "category": "Food & Dining",
            "description": "Zomato dinner biryani treat after midterm exams",
            "date": today.replace(day=15),
            "classification": "want",
            "recurring": False
        },
        {
            "amount": 299.0,
            "type": "expense",
            "category": "Entertainment",
            "description": "Spotify & YouTube Premium student pack",
            "date": today.replace(day=16),
            "classification": "want",
            "recurring": True
        },
        {
            "amount": 350.0,
            "type": "expense",
            "category": "Healthcare",
            "description": "Campus clinic medicines & vitamins",
            "date": today.replace(day=18),
            "classification": "need",
            "recurring": False
        },

        # --- Previous Month Transactions (for trend & Smart Coach comparisons) ---
        {
            "amount": 12000.0,
            "type": "income",
            "category": "Pocket Money / Allowance",
            "description": "Last month parental allowance",
            "date": today - timedelta(days=32),
            "classification": "need",
            "recurring": True
        },
        {
            "amount": 5000.0,
            "type": "income",
            "category": "Part-time / Freelance",
            "description": "Web design gig stipend",
            "date": today - timedelta(days=28),
            "classification": "saving",
            "recurring": False
        },
        {
            "amount": 5500.0,
            "type": "expense",
            "category": "Hostel & Rent",
            "description": "Hostel room rent",
            "date": today - timedelta(days=30),
            "classification": "need",
            "recurring": True
        },
        {
            "amount": 1400.0,
            "type": "expense",
            "category": "Food & Dining",
            "description": "Mess card fee",
            "date": today - timedelta(days=29),
            "classification": "need",
            "recurring": True
        },
        {
            "amount": 1200.0,
            "type": "expense",
            "category": "Food & Dining",
            "description": "Weekend dining out",
            "date": today - timedelta(days=25),
            "classification": "want",
            "recurring": False
        },
        {
            "amount": 500.0,
            "type": "expense",
            "category": "Entertainment",
            "description": "Movie tickets with hostel mates",
            "date": today - timedelta(days=22),
            "classification": "want",
            "recurring": False
        },
        {
            "amount": 800.0,
            "type": "expense",
            "category": "Transport & Travel",
            "description": "Metro recharge",
            "date": today - timedelta(days=27),
            "classification": "need",
            "recurring": True
        }
    ]

    for item in transactions_data:
        t = Transaction(
            user_id=user.id,
            amount=item["amount"],
            transaction_type=item["type"],
            category=item["category"],
            description=item["description"],
            transaction_date=item["date"],
            need_or_want=item["classification"],
            is_recurring=item["recurring"]
        )
        db.add(t)

    # 3. Add Budgets for Current Month
    budgets_data = [
        {"category": "Overall", "limit": 14000.0},
        {"category": "Food & Dining", "limit": 3500.0},
        {"category": "Tech & Gadgets", "limit": 2000.0},
        {"category": "Entertainment", "limit": 1000.0},
        {"category": "Transport & Travel", "limit": 1200.0},
        {"category": "Books & Academics", "limit": 1500.0}
    ]
    for b in budgets_data:
        db.add(Budget(
            user_id=user.id,
            category=b["category"],
            monthly_limit=b["limit"],
            month=curr_month,
            year=curr_year
        ))

    # 4. Add Realistic Savings Goals
    goal1 = SavingsGoal(
        user_id=user.id,
        title="MacBook Air M3 for Final Year Project",
        target_amount=89900.0,
        current_amount=36500.0,
        target_date=today + timedelta(days=120),
        category="Tech & Gadgets",
        status="active"
    )
    db.add(goal1)
    db.flush()

    db.add(GoalContribution(
        goal_id=goal1.id,
        user_id=user.id,
        amount=15000.0,
        note="Summer internship stipend deposit",
        contribution_date=today - timedelta(days=40)
    ))
    db.add(GoalContribution(
        goal_id=goal1.id,
        user_id=user.id,
        amount=21500.0,
        note="Saved from freelance development & scholarship",
        contribution_date=today - timedelta(days=10)
    ))

    goal2 = SavingsGoal(
        user_id=user.id,
        title="Goa Graduation Trip with Friends",
        target_amount=12000.0,
        current_amount=7200.0,
        target_date=today + timedelta(days=60),
        category="Travel",
        status="active"
    )
    db.add(goal2)
    db.flush()

    db.add(GoalContribution(
        goal_id=goal2.id,
        user_id=user.id,
        amount=7200.0,
        note="Initial group trip deposit",
        contribution_date=today - timedelta(days=15)
    ))

    goal3 = SavingsGoal(
        user_id=user.id,
        title="AWS Solutions Architect Certification Exam",
        target_amount=13000.0,
        current_amount=13000.0,
        target_date=today + timedelta(days=15),
        category="Education",
        status="completed"
    )
    db.add(goal3)

    # 5. Add Challenges
    db.add(Challenge(
        user_id=user.id,
        title="Zero Food Delivery Week",
        description="Eat only at the college mess or cook; no Zomato or Swiggy orders for 7 days.",
        category="Food & Dining",
        target_amount=0.0,
        start_date=today - timedelta(days=2),
        end_date=today + timedelta(days=5),
        status="active"
    ))

    db.add(Challenge(
        user_id=user.id,
        title="Weekend Discretionary Cap under ₹500",
        description="Keep all non-essential shopping and entertainment under ₹500 this weekend.",
        category="All Non-Essentials",
        target_amount=500.0,
        start_date=today - timedelta(days=5),
        end_date=today + timedelta(days=2),
        status="active"
    ))

    # Set user's emergency reserve for survival mode
    user.monthly_reserved_amount = 2500.0

    db.commit()


@router.post("/seed")
def seed_current_user_demo_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seed the authenticated user's account with realistic college demo data."""
    populate_student_demo_data(current_user, db)
    return {"status": "success", "message": "Demo data populated successfully!"}


@router.post("/login-demo", response_model=Token)
def login_as_demo_user(db: Session = Depends(get_db)):
    """One-click instant login as demo student with pre-populated realistic data."""
    demo_email = "alex.cse@pennypilot.in"
    demo_user = db.query(User).filter(User.email == demo_email).first()

    if not demo_user:
        demo_user = User(
            name="Alex Sharma (B.Tech CSE)",
            email=demo_email,
            password_hash=hash_password("demopennypilot"),
            monthly_reserved_amount=2500.0
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

    # Populate data for the demo user
    populate_student_demo_data(demo_user, db)

    token = create_access_token(data={"sub": str(demo_user.id), "email": demo_user.email})
    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(demo_user)
    )
