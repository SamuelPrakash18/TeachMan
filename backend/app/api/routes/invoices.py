"""Invoice routes.

Tutors manage invoices for their own business. Parents see read-only invoices
where they are the linked payer. Every query is scoped to the caller's business
or to the parent's own rows.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.finance import Invoice, InvoiceItem, Payment
from app.models.student import ParentStudentLink, Student
from app.models.user import Parent, Tutor, User
from app.schemas.finance import InvoiceIn, InvoiceItemOut, InvoiceOut, InvoiceUpdate
from app.services.invoice_service import days_overdue, next_invoice_number, recalc_invoice

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

INVOICE_NOT_FOUND_DETAIL = "Invoice not found"
CLOSED_STATUSES = ("paid", "cancelled", "draft")


def _caller_business(db: Session, user: User) -> Business:
    business = db.scalar(
        select(Business).join(Tutor, Tutor.id == Business.tutor_id).where(Tutor.user_id == user.id)
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


def _caller_parent(db: Session, user: User) -> Parent:
    parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent profile not found")
    return parent


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _load_for_caller(db: Session, user: User, invoice_id: uuid.UUID) -> Invoice:
    """Tutor: invoice of own business. Parent: invoice where they are the payer."""
    if user.role == "tutor":
        business = _caller_business(db, user)
        stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.business_id == business.id)
    elif user.role == "parent":
        parent = _caller_parent(db, user)
        stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.parent_id == parent.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    invoice = db.scalar(stmt)
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND_DETAIL)
    return invoice


def _load_owned(db: Session, business: Business, invoice_id: uuid.UUID) -> Invoice:
    invoice = db.scalar(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.business_id == business.id)
    )
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND_DETAIL)
    return invoice


def _to_out(db: Session, invoice: Invoice, today: date) -> InvoiceOut:
    student = db.get(Student, invoice.student_id)
    parent_name = None
    if invoice.parent_id is not None:
        parent_name = db.scalar(select(Parent.display_name).where(Parent.id == invoice.parent_id))
    items = db.scalars(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id)).all()

    total = int(invoice.total_paise or 0)
    paid = int(invoice.paid_paise or 0)
    return InvoiceOut(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        student_id=invoice.student_id,
        student_name=student.name if student else "",
        parent_name=parent_name,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        total_paise=total,
        paid_paise=paid,
        outstanding_paise=total - paid,
        status=invoice.status,
        days_overdue=days_overdue(invoice, today),
        items=[
            InvoiceItemOut(
                description=item.description,
                quantity=item.quantity,
                unit_paise=item.unit_paise,
                amount_paise=item.amount_paise,
            )
            for item in items
        ],
    )


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status_filter: str | None = Query(default=None, alias="status", max_length=20),
    overdue: bool | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InvoiceOut]:
    today = date.today()
    stmt = select(Invoice)

    if user.role == "tutor":
        business = _caller_business(db, user)
        stmt = stmt.where(Invoice.business_id == business.id)
    elif user.role == "parent":
        parent = _caller_parent(db, user)
        stmt = stmt.where(Invoice.parent_id == parent.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter)
    if overdue:
        stmt = stmt.where(
            Invoice.due_date < today,
            Invoice.status.notin_(CLOSED_STATUSES),
            Invoice.total_paise > Invoice.paid_paise,
        )
    if q and q.strip():
        matching_students = select(Student.id).where(
            Student.name.ilike(f"%{_escape_like(q.strip())}%", escape="\\")
        )
        stmt = stmt.where(Invoice.student_id.in_(matching_students))

    invoices = db.scalars(stmt.order_by(Invoice.due_date, Invoice.invoice_number)).all()
    return [_to_out(db, invoice, today) for invoice in invoices]


@router.post("", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
def create_invoice(
    body: InvoiceIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> InvoiceOut:
    business = _caller_business(db, user)

    student = db.scalar(
        select(Student).where(
            Student.id == body.student_id,
            Student.business_id == business.id,
            Student.deleted_at.is_(None),
        )
    )
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    if body.parent_id is not None:
        linked = db.scalar(
            select(ParentStudentLink.id).where(
                ParentStudentLink.parent_id == body.parent_id,
                ParentStudentLink.student_id == student.id,
            )
        )
        if linked is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent is not linked to this student",
            )

    line_items = [
        (item, item.quantity * item.unit_paise) for item in body.items
    ]
    total = sum(amount for _, amount in line_items)

    invoice = Invoice(
        id=uuid.uuid4(),
        business_id=business.id,
        student_id=student.id,
        parent_id=body.parent_id,
        invoice_number=next_invoice_number(db, business.id),
        invoice_date=body.invoice_date,
        due_date=body.due_date,
        total_paise=total,
        paid_paise=0,
        status="issued",
    )
    db.add(invoice)
    for item, amount in line_items:
        db.add(
            InvoiceItem(
                id=uuid.uuid4(),
                invoice_id=invoice.id,
                description=item.description,
                quantity=item.quantity,
                unit_paise=item.unit_paise,
                amount_paise=amount,
            )
        )
    db.flush()
    db.commit()
    return _to_out(db, invoice, date.today())


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InvoiceOut:
    invoice = _load_for_caller(db, user, invoice_id)
    return _to_out(db, invoice, date.today())


@router.put("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: uuid.UUID,
    body: InvoiceUpdate,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> InvoiceOut:
    business = _caller_business(db, user)
    invoice = _load_owned(db, business, invoice_id)

    if invoice.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cancelled invoices cannot be edited")
    if (invoice.paid_paise or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoices with recorded payments cannot be edited",
        )

    if body.due_date is not None:
        if body.due_date < invoice.invoice_date:
            raise HTTPException(
                status_code=422,
                detail="due_date must be on or after invoice_date",
            )
        invoice.due_date = body.due_date
        recalc_invoice(db, invoice)

    db.commit()
    return _to_out(db, invoice, date.today())


@router.post("/{invoice_id}/cancel", response_model=InvoiceOut)
def cancel_invoice(
    invoice_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> InvoiceOut:
    business = _caller_business(db, user)
    invoice = _load_owned(db, business, invoice_id)

    if invoice.status == "cancelled":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invoice is already cancelled")
    if (invoice.paid_paise or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoices with recorded payments cannot be cancelled",
        )

    invoice.status = "cancelled"
    db.commit()
    return _to_out(db, invoice, date.today())


@router.get("/{invoice_id}/receipt")
def get_receipt(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    invoice = _load_for_caller(db, user, invoice_id)
    paid = int(invoice.paid_paise or 0)
    if paid == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No payments recorded for this invoice",
        )

    payments = db.scalars(
        select(Payment)
        .where(Payment.invoice_id == invoice.id, Payment.business_id == invoice.business_id)
        .order_by(Payment.paid_on, Payment.created_at)
    ).all()
    total = int(invoice.total_paise or 0)

    return {
        "receipt_number": invoice.invoice_number,
        "invoice": _to_out(db, invoice, date.today()),
        "payments": [
            {
                "id": payment.id,
                "amount_paise": payment.amount_paise,
                "method": payment.method,
                "reference": payment.reference,
                "paid_on": payment.paid_on,
            }
            for payment in payments
        ],
        "total_paise": total,
        "paid_paise": paid,
        "outstanding_paise": total - paid,
    }
