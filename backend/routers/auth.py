from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.database import get_db
from backend.models import User
from backend.schemas import UserCreate, UserLogin, UserOut, Token, UserUpdate
from backend.security import hash_password, verify_password, create_access_token, get_current_user
from backend.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new student user."""
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Hash password using bcrypt
    hashed = hash_password(user_in.password)
    new_user = User(
        name=user_in.name.strip(),
        email=user_in.email.lower().strip(),
        password_hash=hashed,
        monthly_reserved_amount=0.0
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create JWT
    token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email},
        expires_delta=token_expires
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(new_user)
    )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a student user with email and password."""
    user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=token_expires
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve current authenticated user profile."""
    return UserOut.model_validate(current_user)


@router.put("/profile", response_model=UserOut)
def update_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update profile details such as name or emergency reserved amount for survival mode."""
    if update_data.name is not None:
        current_user.name = update_data.name.strip()
    if update_data.monthly_reserved_amount is not None:
        current_user.monthly_reserved_amount = max(0.0, update_data.monthly_reserved_amount)

    db.commit()
    db.refresh(current_user)
    return UserOut.model_validate(current_user)
