import io
import csv
import math
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from backend.database import get_db
from backend.models import Transaction, User
from backend.schemas import (
    TransactionCreate,
    TransactionUpdate,
    TransactionOut,
    TransactionListResponse
)
from backend.security import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=100),
    search: Optional[str] = None,
    transaction_type: Optional[str] = Query(None, pattern="^(income|expense)$"),
    category: Optional[str] = None,
    need_or_want: Optional[str] = Query(None, pattern="^(need|want|saving)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: Optional[str] = Query("date", pattern="^(date|amount)$"),
    order: Optional[str] = Query("desc", pattern="^(asc|desc)$")
):
    """Retrieve filtered, searched, sorted, and paginated transactions for the current user."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    # Search filter
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (Transaction.description.ilike(search_fmt)) |
            (Transaction.category.ilike(search_fmt))
        )

    # Type filter
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    # Category filter
    if category and category != "all":
        query = query.filter(Transaction.category == category)

    # Need vs Want filter
    if need_or_want and need_or_want != "all":
        query = query.filter(Transaction.need_or_want == need_or_want)

    # Date ranges
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    total = query.count()

    # Sorting
    sort_col = Transaction.amount if sort_by == "amount" else Transaction.transaction_date
    if order == "asc":
        query = query.order_by(asc(sort_col), asc(Transaction.id))
    else:
        query = query.order_by(desc(sort_col), desc(Transaction.id))

    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return TransactionListResponse(
        items=[TransactionOut.model_validate(tx) for tx in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    tx_in: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new income or expense transaction."""
    tx = Transaction(
        user_id=current_user.id,
        amount=round(float(tx_in.amount), 2),
        transaction_type=tx_in.transaction_type,
        category=tx_in.category.strip(),
        description=tx_in.description.strip() if tx_in.description else "",
        transaction_date=tx_in.transaction_date,
        need_or_want=tx_in.need_or_want,
        is_recurring=tx_in.is_recurring
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return TransactionOut.model_validate(tx)


@router.get("/export/csv")
def export_transactions_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[str] = None
):
    """Export transactions to CSV for accounting and student record-keeping."""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if transaction_type in ["income", "expense"]:
        query = query.filter(Transaction.transaction_type == transaction_type)

    transactions = query.order_by(desc(Transaction.transaction_date)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    # Header
    writer.writerow([
        "Transaction ID",
        "Date",
        "Type",
        "Category",
        "Description",
        "Amount (INR)",
        "Classification",
        "Recurring"
    ])

    for tx in transactions:
        writer.writerow([
            tx.id,
            tx.transaction_date.isoformat(),
            tx.transaction_type.capitalize(),
            tx.category,
            tx.description or "",
            f"{tx.amount:.2f}",
            tx.need_or_want.capitalize(),
            "Yes" if tx.is_recurring else "No"
        ])

    csv_data = output.getvalue()
    filename = f"pennypilot_transactions_{date.today().isoformat()}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{tx_id}", response_model=TransactionOut)
def get_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single transaction by ID."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionOut.model_validate(tx)


@router.put("/{tx_id}", response_model=TransactionOut)
def update_transaction(
    tx_id: int,
    tx_in: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing transaction."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if tx_in.amount is not None:
        tx.amount = round(float(tx_in.amount), 2)
    if tx_in.transaction_type is not None:
        tx.transaction_type = tx_in.transaction_type
    if tx_in.category is not None:
        tx.category = tx_in.category.strip()
    if tx_in.description is not None:
        tx.description = tx_in.description.strip()
    if tx_in.transaction_date is not None:
        tx.transaction_date = tx_in.transaction_date
    if tx_in.need_or_want is not None:
        tx.need_or_want = tx_in.need_or_want
    if tx_in.is_recurring is not None:
        tx.is_recurring = tx_in.is_recurring

    db.commit()
    db.refresh(tx)
    return TransactionOut.model_validate(tx)


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a transaction."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == current_user.id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    db.delete(tx)
    db.commit()
    return None
