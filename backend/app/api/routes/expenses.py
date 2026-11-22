"""Expense routes (tutor only, business-scoped).

Only unpaid expenses count as forecast outflows. Paid expenses are financial
history: they cannot be edited or deleted. Deleting is therefore a hard delete
that is allowed only while the expense is still unpaid, so no soft-delete column
is needed.
"""
import calendar
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.finance import Expense
from app.models.user import Tutor, User
from app.schemas.finance import ExpenseIn, ExpenseMarkPaidIn, ExpenseOut, ExpenseUpdate

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

EXPENSE_NOT_FOUND_DETAIL = "Expense not found"
NON_NULLABLE_FIELDS = ("title", "category", "amount_paise", "due_date", "is_recurring")


def _caller_business(db: Session, user: User) -> Business:
    business = db.scalar(
        select(Business).join(Tutor, Tutor.id == Business.tutor_id).where(Tutor.user_id == user.id)
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


def _load_owned(db: Session, business: Business, expense_id: uuid.UUID, lock: bool = False) -> Expense:
    stmt = select(Expense).where(Expense.id == expense_id, Expense.business_id == business.id)
    if lock:
        stmt = stmt.with_for_update()
    expense = db.scalar(stmt)
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=EXPENSE_NOT_FOUND_DETAIL)
    return expense


def _next_month_same_day(day: date) -> date:
    """Same day-of-month in the next calendar month, clamped to that month's length."""
    year = day.year + (1 if day.month == 12 else 0)
    month = 1 if day.month == 12 else day.month + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))


def _to_out(expense: Expense, today: date) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        title=expense.title,
        category=expense.category,
        amount_paise=expense.amount_paise,
        due_date=expense.due_date,
        paid_on=expense.paid_on,
        status=expense.status,
        is_recurring=bool(expense.is_recurring),
        notes=expense.notes,
        overdue=expense.status == "unpaid" and expense.due_date < today,
    )


@router.get("", response_model=list[ExpenseOut])
def list_expenses(
    status_filter: str | None = Query(default=None, alias="status", max_length=10),
    category: str | None = Query(default=None, max_length=20),
    overdue: bool | None = Query(default=None),
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> list[ExpenseOut]:
    today = date.today()
    business = _caller_business(db, user)
    stmt = select(Expense).where(Expense.business_id == business.id)

    if status_filter:
        stmt = stmt.where(Expense.status == status_filter)
    if category:
        stmt = stmt.where(Expense.category == category)
    if overdue:
        stmt = stmt.where(Expense.status == "unpaid", Expense.due_date < today)

    expenses = db.scalars(stmt.order_by(Expense.due_date, Expense.created_at)).all()
    return [_to_out(expense, today) for expense in expenses]


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> ExpenseOut:
    business = _caller_business(db, user)
    expense = Expense(
        id=uuid.uuid4(),
        business_id=business.id,
        title=body.title,
        category=body.category,
        amount_paise=body.amount_paise,
        due_date=body.due_date,
        is_recurring=body.is_recurring,
        notes=body.notes,
        status="unpaid",
    )
    db.add(expense)
    db.commit()
    return _to_out(expense, date.today())


@router.put("/{expense_id}", response_model=ExpenseOut)
def update_expense(
    expense_id: uuid.UUID,
    body: ExpenseUpdate,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> ExpenseOut:
    business = _caller_business(db, user)
    expense = _load_owned(db, business, expense_id)

    if expense.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paid expenses are financial history and cannot be edited",
        )

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field in NON_NULLABLE_FIELDS:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be cleared",
            )
        setattr(expense, field, value)

    db.commit()
    return _to_out(expense, date.today())


@router.post("/{expense_id}/mark-paid", response_model=ExpenseOut)
def mark_expense_paid(
    expense_id: uuid.UUID,
    body: ExpenseMarkPaidIn | None = None,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> ExpenseOut:
    today = date.today()
    business = _caller_business(db, user)
    expense = _load_owned(db, business, expense_id, lock=True)

    if expense.status == "paid":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Expense is already paid")

    paid_on = (body.paid_on if body and body.paid_on else None) or today
    expense.status = "paid"
    expense.paid_on = paid_on

    if expense.is_recurring:
        db.add(
            Expense(
                id=uuid.uuid4(),
                business_id=expense.business_id,
                title=expense.title,
                category=expense.category,
                amount_paise=expense.amount_paise,
                due_date=_next_month_same_day(expense.due_date),
                paid_on=None,
                is_recurring=True,
                notes=expense.notes,
                status="unpaid",
            )
        )

    db.commit()
    return _to_out(expense, today)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> None:
    business = _caller_business(db, user)
    expense = _load_owned(db, business, expense_id)

    if expense.status != "unpaid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paid expenses are financial history and cannot be deleted",
        )

    db.delete(expense)
    db.commit()
