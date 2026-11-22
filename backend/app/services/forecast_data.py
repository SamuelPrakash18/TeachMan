"""Database loader for forecast inputs.

Every query is filtered by business_id. The result is plain dicts so the
pure engine in forecast_engine.py never touches the ORM.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CashSnapshot, Expense, Invoice, Student

OPEN_INVOICE_STATUSES = ("issued", "partially_paid", "overdue")


def load_forecast_inputs(db: Session, business_id: uuid.UUID, today: date) -> dict:
    # `today` is accepted for the caller's window logic; the engine maps
    # past-due items onto the forecast start date, so no date filter is applied here.
    opening_cash_paise = db.execute(
        select(CashSnapshot.opening_cash_paise).where(
            CashSnapshot.business_id == business_id
        )
    ).scalar_one_or_none()
    opening = int(opening_cash_paise) if opening_cash_paise is not None else 0

    invoice_rows = db.execute(
        select(
            Invoice.id,
            Student.name,
            Invoice.total_paise,
            Invoice.paid_paise,
            Invoice.due_date,
        )
        .join(Student, Student.id == Invoice.student_id)
        .where(
            Invoice.business_id == business_id,
            Invoice.status.in_(OPEN_INVOICE_STATUSES),
        )
    ).all()

    invoices: list[dict] = []
    for inv_id, student_name, total_paise, paid_paise, due_date in invoice_rows:
        outstanding = int(total_paise) - int(paid_paise)
        if outstanding <= 0:
            continue
        invoices.append(
            {
                "id": str(inv_id),
                "student_name": student_name,
                "outstanding_paise": outstanding,
                "due_date": due_date,
            }
        )

    expense_rows = db.execute(
        select(Expense.id, Expense.title, Expense.amount_paise, Expense.due_date).where(
            Expense.business_id == business_id,
            Expense.status == "unpaid",
        )
    ).all()

    expenses: list[dict] = [
        {
            "id": str(exp_id),
            "title": title,
            "amount_paise": int(amount_paise),
            "due_date": due_date,
        }
        for exp_id, title, amount_paise, due_date in expense_rows
    ]

    return {
        "opening_cash_paise": opening,
        "invoices": invoices,
        "expenses": expenses,
    }
