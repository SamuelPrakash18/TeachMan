"""Invoice helpers: payment recalculation, numbering and overdue logic."""
from __future__ import annotations

import re
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.business import Business
from app.models.finance import Invoice, Payment

_NUMBER_RE = re.compile(r"(\d+)$")


def recalc_invoice(db: Session, invoice: Invoice) -> Invoice:
    """Recompute paid/outstanding totals and status for an invoice.

    Cancelled and draft invoices keep their status; only paid_paise changes.
    """
    db.flush()
    paid = db.execute(
        select(func.coalesce(func.sum(Payment.amount_paise), 0)).where(
            Payment.invoice_id == invoice.id
        )
    ).scalar_one()
    paid = int(paid or 0)
    invoice.paid_paise = paid

    if invoice.status in ("draft", "cancelled"):
        return invoice

    total = int(invoice.total_paise or 0)
    outstanding = total - paid
    today = date.today()

    if outstanding == 0 and total > 0:
        invoice.status = "paid"
    elif paid > 0:
        invoice.status = "partially_paid"
    elif invoice.due_date is not None and invoice.due_date < today:
        invoice.status = "overdue"
    else:
        invoice.status = "issued"
    return invoice


def next_invoice_number(db: Session, business_id) -> str:
    """Return the next 'INV-NNNNNN' number for a business.

    Locks the Business row so concurrent requests serialise on numbering.
    """
    db.execute(
        select(Business).where(Business.id == business_id).with_for_update()
    ).scalar_one_or_none()

    numbers = db.execute(
        select(Invoice.invoice_number).where(Invoice.business_id == business_id)
    ).scalars().all()

    highest = 0
    for number in numbers:
        match = _NUMBER_RE.search(number or "")
        if match:
            highest = max(highest, int(match.group(1)))
    return f"INV-{highest + 1:06d}"


def days_overdue(invoice: Invoice, today: date) -> int:
    """Number of whole days past due; 0 if the invoice is not overdue."""
    if invoice.status in ("paid", "cancelled", "draft"):
        return 0
    if invoice.due_date is None or invoice.due_date >= today:
        return 0
    if (invoice.total_paise or 0) - (invoice.paid_paise or 0) <= 0:
        return 0
    return (today - invoice.due_date).days
