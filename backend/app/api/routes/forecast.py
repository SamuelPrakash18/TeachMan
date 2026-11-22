import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.db.session import get_db
from app.models import CashSnapshot, Invoice, Student
from app.models.business import Business
from app.models.user import Tutor, User
from app.schemas.forecast import CashSnapshotIn, CashSnapshotOut, ForecastResponse, SimulateIn
from app.services.forecast_data import OPEN_INVOICE_STATUSES, load_forecast_inputs
from app.services.forecast_engine import build_forecast, compare_forecasts, recommendations

router = APIRouter(prefix="/api/forecast", tags=["forecast"])

ALLOWED_WINDOWS = (30, 60, 90)
NOT_FOUND_INVOICE = "Invoice not found"


def _caller_business(db: Session, user: User) -> Business:
    business = db.scalar(
        select(Business).join(Tutor, Tutor.id == Business.tutor_id).where(Tutor.user_id == user.id)
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


def _iso(value):
    """Recursively convert dates and UUIDs into JSON-safe strings."""
    if isinstance(value, dict):
        return {key: _iso(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_iso(item) for item in value]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _summary(forecast: dict) -> dict:
    return {key: value for key, value in forecast.items() if key != "daily"}


def _outstanding(invoice: Invoice) -> int:
    return int(invoice.total_paise) - int(invoice.paid_paise)


@router.get("", response_model=ForecastResponse)
def get_forecast(
    days: int = Query(default=30),
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> dict:
    if days not in ALLOWED_WINDOWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="days must be 30, 60 or 90",
        )
    business = _caller_business(db, user)
    today = date.today()
    inputs = load_forecast_inputs(db, business.id, today)
    forecast = build_forecast(
        inputs["opening_cash_paise"],
        today,
        days,
        inputs["invoices"],
        inputs["expenses"],
    )
    return _iso(forecast)


@router.get("/cash-snapshot", response_model=CashSnapshotOut)
def get_cash_snapshot(
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> CashSnapshotOut:
    business = _caller_business(db, user)
    row = db.scalar(select(CashSnapshot).where(CashSnapshot.business_id == business.id))
    if row is None:
        return CashSnapshotOut(opening_cash_paise=0, as_of_date=None)
    return CashSnapshotOut(
        opening_cash_paise=int(row.opening_cash_paise),
        as_of_date=row.as_of_date,
    )


@router.put("/cash-snapshot", response_model=CashSnapshotOut)
def put_cash_snapshot(
    body: CashSnapshotIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> CashSnapshotOut:
    business = _caller_business(db, user)
    row = db.scalar(select(CashSnapshot).where(CashSnapshot.business_id == business.id))
    if row is None:
        row = CashSnapshot(business_id=business.id)
        db.add(row)
    row.opening_cash_paise = body.opening_cash_paise
    row.as_of_date = body.as_of_date or date.today()
    db.commit()
    db.refresh(row)
    return CashSnapshotOut(
        opening_cash_paise=int(row.opening_cash_paise),
        as_of_date=row.as_of_date,
    )


@router.post("/simulate")
def simulate_delay(
    body: SimulateIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> dict:
    # Read-only: this endpoint computes both forecasts in memory and writes nothing.
    business = _caller_business(db, user)
    invoice = db.scalar(
        select(Invoice).where(
            Invoice.id == body.invoice_id,
            Invoice.business_id == business.id,
        )
    )
    if (
        invoice is None
        or invoice.status in ("cancelled", "draft")
        or _outstanding(invoice) <= 0
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_INVOICE)

    today = date.today()
    inputs = load_forecast_inputs(db, business.id, today)
    original = build_forecast(
        inputs["opening_cash_paise"],
        today,
        body.days,
        inputs["invoices"],
        inputs["expenses"],
    )

    simulated_due = invoice.due_date + timedelta(days=body.delay_days)
    simulated = build_forecast(
        inputs["opening_cash_paise"],
        today,
        body.days,
        inputs["invoices"],
        inputs["expenses"],
        overrides={str(invoice.id): simulated_due},
    )

    comparison = compare_forecasts(original, simulated)
    tips = recommendations(comparison)

    return {
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "original_expected_date": max(invoice.due_date, today).isoformat(),
        "simulated_expected_date": max(simulated_due, today).isoformat(),
        "original": _iso(_summary(original)),
        "simulated": _iso(_summary(simulated)),
        "comparison": _iso(comparison),
        "recommendations": tips,
        "daily_original": _iso(original["daily"]),
        "daily_simulated": _iso(simulated["daily"]),
    }


@router.get("/cash-explanation-context")
def cash_explanation_context(
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> dict:
    # Plain facts only; no AI call is made here.
    business = _caller_business(db, user)
    today = date.today()
    inputs = load_forecast_inputs(db, business.id, today)
    forecast = build_forecast(
        inputs["opening_cash_paise"],
        today,
        30,
        inputs["invoices"],
        inputs["expenses"],
    )
    summary = _iso(_summary(forecast))

    top_expenses = sorted(
        inputs["expenses"], key=lambda exp: exp["amount_paise"], reverse=True
    )[:5]
    expense_facts = [
        {
            "title": exp["title"],
            "amount_paise": exp["amount_paise"],
            "due_date": _iso(exp["due_date"]),
        }
        for exp in top_expenses
    ]

    invoice_rows = db.execute(
        select(
            Invoice.invoice_number,
            Student.name,
            Invoice.total_paise,
            Invoice.paid_paise,
            Invoice.due_date,
        )
        .join(Student, Student.id == Invoice.student_id)
        .where(
            Invoice.business_id == business.id,
            Invoice.status.in_(OPEN_INVOICE_STATUSES),
        )
    ).all()

    invoice_facts: list[dict] = []
    for invoice_number, student_name, total_paise, paid_paise, due_date in invoice_rows:
        outstanding = int(total_paise) - int(paid_paise)
        if outstanding <= 0:
            continue
        invoice_facts.append(
            {
                "invoice_number": invoice_number,
                "student_name": student_name,
                "outstanding_paise": outstanding,
                "due_date": due_date.isoformat(),
                "days_overdue": max(0, (today - due_date).days),
            }
        )
    invoice_facts.sort(key=lambda row: row["outstanding_paise"], reverse=True)

    return {
        "forecast_30_day": summary,
        "shortage_date": summary["shortage_date"],
        "top_unpaid_expenses": expense_facts,
        "top_outstanding_invoices": invoice_facts[:5],
    }
