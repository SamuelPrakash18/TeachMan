"""Payment routes: tutor-recorded payments, parent UPI claims and tutor review.

Parents can only submit claims. A claim becomes a Payment row only when a
tutor approves it. Screenshots are never treated as proof of payment.
"""
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_parent, require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.finance import Invoice, Payment, PaymentClaim
from app.models.system import Notification
from app.models.user import Parent, Tutor, User
from app.schemas.finance import PaymentClaimIn, PaymentClaimOut, PaymentIn, PaymentOut
from app.services.invoice_service import recalc_invoice

router = APIRouter(prefix="/api/payments", tags=["payments"])

INVOICE_NOT_FOUND_DETAIL = "Invoice not found"
CLAIM_NOT_FOUND_DETAIL = "Payment claim not found"
DUPLICATE_REFERENCE_DETAIL = "A payment with this reference and method already exists"
UNPAYABLE_STATUSES = ("draft", "cancelled")
OPEN_CLAIM_STATUSES = ("pending", "under_review")


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


def _tutor_user_id(db: Session, business_id: uuid.UUID) -> uuid.UUID | None:
    return db.scalar(
        select(Tutor.user_id).join(Business, Business.tutor_id == Tutor.id).where(Business.id == business_id)
    )


def _parent_user_id(db: Session, parent_id: uuid.UUID) -> uuid.UUID | None:
    return db.scalar(select(Parent.user_id).where(Parent.id == parent_id))


def _notify(db: Session, user_id: uuid.UUID | None, title: str, body: str) -> None:
    if user_id is None:
        return
    db.add(Notification(user_id=user_id, title=title, body=body))


def _fmt_paise(amount: int) -> str:
    rupees, paise = divmod(int(amount), 100)
    return f"Rs {rupees:,}.{paise:02d}"


def _outstanding(invoice: Invoice) -> int:
    return int(invoice.total_paise or 0) - int(invoice.paid_paise or 0)


def _lock_invoice(db: Session, business_id: uuid.UUID, invoice_id: uuid.UUID) -> Invoice:
    invoice = db.scalar(
        select(Invoice)
        .where(Invoice.id == invoice_id, Invoice.business_id == business_id)
        .with_for_update()
    )
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND_DETAIL)
    return invoice


def _clean_reference(reference: str | None) -> str | None:
    if reference is None:
        return None
    return reference.strip() or None


def _ensure_reference_free(db: Session, business_id: uuid.UUID, method: str, reference: str | None) -> None:
    if reference is None:
        return
    exists = db.scalar(
        select(Payment.id).where(
            Payment.business_id == business_id,
            Payment.method == method,
            Payment.reference == reference,
        )
    )
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_REFERENCE_DETAIL)


def _payment_out(payment: Payment, invoice_number: str) -> PaymentOut:
    return PaymentOut(
        id=payment.id,
        invoice_id=payment.invoice_id,
        invoice_number=invoice_number,
        amount_paise=payment.amount_paise,
        method=payment.method,
        reference=payment.reference,
        paid_on=payment.paid_on,
    )


def _claim_out(claim: PaymentClaim, invoice_number: str, parent_name: str | None) -> PaymentClaimOut:
    return PaymentClaimOut(
        id=claim.id,
        invoice_id=claim.invoice_id,
        invoice_number=invoice_number,
        parent_name=parent_name,
        amount_paise=claim.amount_paise,
        upi_reference=claim.upi_reference,
        status=claim.status,
        submitted_at=claim.submitted_at,
        reviewed_at=claim.reviewed_at,
    )


def _claim_detail(db: Session, claim: PaymentClaim) -> PaymentClaimOut:
    invoice = db.get(Invoice, claim.invoice_id)
    parent = db.get(Parent, claim.parent_id)
    return _claim_out(
        claim,
        invoice.invoice_number if invoice else "",
        parent.display_name if parent else None,
    )


def _load_claim(db: Session, business_id: uuid.UUID, claim_id: uuid.UUID) -> PaymentClaim:
    claim = db.scalar(
        select(PaymentClaim).where(
            PaymentClaim.id == claim_id,
            PaymentClaim.business_id == business_id,
        )
    )
    if claim is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CLAIM_NOT_FOUND_DETAIL)
    return claim


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def record_payment(
    body: PaymentIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> PaymentOut:
    business = _caller_business(db, user)
    invoice = _lock_invoice(db, business.id, body.invoice_id)

    if invoice.status in UNPAYABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot record a payment on a {invoice.status} invoice",
        )
    if body.amount_paise > _outstanding(invoice):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment amount exceeds the outstanding balance",
        )

    reference = _clean_reference(body.reference)
    _ensure_reference_free(db, business.id, body.method, reference)

    payment = Payment(
        id=uuid.uuid4(),
        business_id=business.id,
        invoice_id=invoice.id,
        amount_paise=body.amount_paise,
        method=body.method,
        reference=reference,
        paid_on=body.paid_on,
        recorded_by_user_id=user.id,
    )
    try:
        db.add(payment)
        db.flush()
        recalc_invoice(db, invoice)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_REFERENCE_DETAIL)

    return _payment_out(payment, invoice.invoice_number)


@router.get("", response_model=list[PaymentOut])
def list_payments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaymentOut]:
    stmt = select(Payment, Invoice.invoice_number).join(Invoice, Invoice.id == Payment.invoice_id)

    if user.role == "tutor":
        business = _caller_business(db, user)
        stmt = stmt.where(Payment.business_id == business.id)
    elif user.role == "parent":
        parent = _caller_parent(db, user)
        stmt = stmt.where(Invoice.parent_id == parent.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    rows = db.execute(stmt.order_by(Payment.paid_on.desc(), Payment.created_at.desc())).all()
    return [_payment_out(payment, number) for payment, number in rows]


@router.post("/claims", response_model=PaymentClaimOut, status_code=status.HTTP_201_CREATED)
def submit_claim(
    body: PaymentClaimIn,
    user: User = Depends(require_parent),
    db: Session = Depends(get_db),
) -> PaymentClaimOut:
    parent = _caller_parent(db, user)
    invoice = db.scalar(
        select(Invoice).where(Invoice.id == body.invoice_id, Invoice.parent_id == parent.id)
    )
    if invoice is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVOICE_NOT_FOUND_DETAIL)
    if invoice.status in UNPAYABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Payments cannot be claimed on a {invoice.status} invoice",
        )
    if body.amount_paise > _outstanding(invoice):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Claimed amount exceeds the outstanding balance",
        )

    claim = PaymentClaim(
        id=uuid.uuid4(),
        business_id=invoice.business_id,
        invoice_id=invoice.id,
        parent_id=parent.id,
        amount_paise=body.amount_paise,
        upi_reference=body.upi_reference,
        status="pending",
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(claim)
    _notify(
        db,
        _tutor_user_id(db, invoice.business_id),
        "Payment claim submitted",
        f"{parent.display_name} reported a UPI payment of {_fmt_paise(body.amount_paise)} "
        f"for invoice {invoice.invoice_number}. Please verify it.",
    )
    db.commit()
    return _claim_out(claim, invoice.invoice_number, parent.display_name)


@router.get("/claims", response_model=list[PaymentClaimOut])
def list_claims(
    status_filter: str | None = Query(default=None, alias="status", max_length=20),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaymentClaimOut]:
    stmt = (
        select(PaymentClaim, Invoice.invoice_number, Parent.display_name)
        .join(Invoice, Invoice.id == PaymentClaim.invoice_id)
        .join(Parent, Parent.id == PaymentClaim.parent_id)
    )

    if user.role == "tutor":
        business = _caller_business(db, user)
        stmt = stmt.where(PaymentClaim.business_id == business.id)
    elif user.role == "parent":
        parent = _caller_parent(db, user)
        stmt = stmt.where(PaymentClaim.parent_id == parent.id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if status_filter:
        stmt = stmt.where(PaymentClaim.status == status_filter)

    rows = db.execute(stmt.order_by(PaymentClaim.submitted_at.desc())).all()
    return [_claim_out(claim, number, parent_name) for claim, number, parent_name in rows]


@router.post("/claims/{claim_id}/review", response_model=PaymentClaimOut)
def review_claim(
    claim_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> PaymentClaimOut:
    business = _caller_business(db, user)
    claim = _load_claim(db, business.id, claim_id)

    if claim.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending claims can be put under review")

    claim.status = "under_review"
    db.commit()
    return _claim_detail(db, claim)


@router.post("/claims/{claim_id}/approve", response_model=PaymentClaimOut)
def approve_claim(
    claim_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> PaymentClaimOut:
    business = _caller_business(db, user)
    claim = _load_claim(db, business.id, claim_id)
    invoice = _lock_invoice(db, business.id, claim.invoice_id)
    db.refresh(claim)

    if claim.status not in OPEN_CLAIM_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Claim has already been decided")
    if invoice.status in UNPAYABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot approve a claim on a {invoice.status} invoice",
        )
    if claim.amount_paise > _outstanding(invoice):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Claimed amount exceeds the outstanding balance",
        )
    _ensure_reference_free(db, business.id, "upi", claim.upi_reference)

    payment = Payment(
        id=uuid.uuid4(),
        business_id=business.id,
        invoice_id=invoice.id,
        amount_paise=claim.amount_paise,
        method="upi",
        reference=claim.upi_reference,
        paid_on=date.today(),
        recorded_by_user_id=user.id,
    )
    try:
        db.add(payment)
        db.flush()
        claim.status = "verified"
        claim.reviewed_at = datetime.now(timezone.utc)
        claim.payment_id = payment.id
        recalc_invoice(db, invoice)
        _notify(
            db,
            _parent_user_id(db, claim.parent_id),
            "Payment verified",
            f"Your payment of {_fmt_paise(claim.amount_paise)} for invoice "
            f"{invoice.invoice_number} has been verified.",
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=DUPLICATE_REFERENCE_DETAIL)

    return _claim_detail(db, claim)


@router.post("/claims/{claim_id}/reject", response_model=PaymentClaimOut)
def reject_claim(
    claim_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> PaymentClaimOut:
    business = _caller_business(db, user)
    claim = _load_claim(db, business.id, claim_id)

    if claim.status not in OPEN_CLAIM_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Claim has already been decided")

    invoice = db.get(Invoice, claim.invoice_id)
    claim.status = "rejected"
    claim.reviewed_at = datetime.now(timezone.utc)
    _notify(
        db,
        _parent_user_id(db, claim.parent_id),
        "Payment claim declined",
        f"Your payment claim of {_fmt_paise(claim.amount_paise)} for invoice "
        f"{invoice.invoice_number if invoice else ''} was declined. Please contact your tutor.",
    )
    db.commit()
    return _claim_detail(db, claim)
