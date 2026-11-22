import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.finance import Invoice
from app.models.student import Student
from app.models.user import Parent, Tutor, User
from app.schemas.ai import AssistantIn, AssistantOut, CashExplainOut, ReminderIn, ReminderOut
from app.services.ai_service import (
    FORECAST_DAYS,
    TOP_N,
    answer_question,
    build_business_facts,
    draft_reminder,
    explain_cashflow,
)
from app.services.forecast_data import load_forecast_inputs
from app.services.forecast_engine import build_forecast

router = APIRouter(prefix="/api/ai", tags=["ai"])



def _caller_business(db: Session, user: User) -> Business:
    business = db.scalar(
        select(Business).join(Tutor, Tutor.id == Business.tutor_id).where(Tutor.user_id == user.id)
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


@router.post("/reminder", response_model=ReminderOut)
def create_reminder(
    body: ReminderIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> ReminderOut:
    business = _caller_business(db, user)
    invoice = db.scalar(
        select(Invoice).where(
            Invoice.id == body.invoice_id,
            Invoice.business_id == business.id,
        )
    )
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

    student = db.scalar(select(Student).where(Student.id == invoice.student_id))
    student_name = student.name if student is not None else ""

    parent_name: str | None = None
    if invoice.parent_id is not None:
        parent_name = db.scalar(select(Parent.display_name).where(Parent.id == invoice.parent_id))

    outstanding = int(invoice.total_paise) - int(invoice.paid_paise)
    days_overdue = max((date.today() - invoice.due_date).days, 0)

    text, source = draft_reminder(
        tone=body.tone,
        student_name=student_name,
        parent_name=parent_name,
        invoice_number=invoice.invoice_number,
        outstanding_paise=outstanding,
        due_date_iso=invoice.due_date.isoformat(),
        days_overdue=days_overdue,
    )
    return ReminderOut(text=text, source=source)


@router.post("/cashflow-explanation", response_model=CashExplainOut)
def cashflow_explanation(
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> CashExplainOut:
    business = _caller_business(db, user)
    today = date.today()
    inputs = load_forecast_inputs(db, business.id, today)
    forecast = build_forecast(
        opening_cash_paise=inputs["opening_cash_paise"],
        start_date=today,
        days=FORECAST_DAYS,
        invoices=inputs["invoices"],
        expenses=inputs["expenses"],
    )
    facts = {
        "start_date": forecast["start_date"].isoformat(),
        "days": forecast["days"],
        "shortage_date": forecast["shortage_date"].isoformat() if forecast["shortage_date"] else None,
        "projected_closing_paise": forecast["projected_closing_paise"],
        "lowest_closing_paise": forecast["lowest_closing_paise"],
        "expected_collections_paise": forecast["expected_collections_paise"],
        "expected_expenses_paise": forecast["expected_expenses_paise"],
        "top_outflows": [
            {"title": item["title"], "amount_paise": item["amount_paise"]}
            for item in sorted(
                forecast["outflow_items"], key=lambda i: i["amount_paise"], reverse=True
            )[:TOP_N]
        ],
    }
    text, source = explain_cashflow(facts)
    return CashExplainOut(text=text, source=source)


@router.post("/assistant", response_model=AssistantOut)
def assistant(
    body: AssistantIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> AssistantOut:
    business = _caller_business(db, user)
    facts = build_business_facts(db, business.id)
    answer, source = answer_question(body.question, facts)
    return AssistantOut(answer=answer, source=source)
