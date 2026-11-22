from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import verify_password
from app.db.session import get_db
from app.models.business import Business
from app.models.finance import Expense, Invoice, PaymentClaim
from app.models.student import ParentStudentLink, Student
from app.models.system import AccountDeletionRequest, AccountStatusHistory, ActivityLog
from app.models.teaching import Enrollment
from app.models.user import Parent, Tutor, User

router = APIRouter(prefix="/api/account", tags=["account"])

CONFIRMATION_PHRASE = "DELETE MY ACCOUNT"
RETENTION_NOTICE = (
    "Financial records and outstanding obligations are retained for accounting and "
    "dispute resolution. Deleting your account does not cancel outstanding fees or "
    "reverse submitted payments."
)
OPEN_CLAIM_STATUSES = ("pending", "under_review")
PASSWORD_INCORRECT_DETAIL = "Password is incorrect"
NO_PENDING_REQUEST_DETAIL = "No pending deletion request"
PROFILE_MISSING_DETAIL = "Profile not found"


class SettingsUpdateIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)


class PasswordIn(BaseModel):
    password: str = Field(min_length=1)


class DeletionConfirmIn(BaseModel):
    password: str = Field(min_length=1)
    confirmation_phrase: str


def _tutor_row(db: Session, user: User) -> Tutor:
    tutor = db.scalar(select(Tutor).where(Tutor.user_id == user.id))
    if tutor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_MISSING_DETAIL)
    return tutor


def _parent_row(db: Session, user: User) -> Parent:
    parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_MISSING_DETAIL)
    return parent


def _identity(db: Session, user: User) -> tuple[str | None, str | None]:
    if user.role == "tutor":
        tutor = db.scalar(select(Tutor).where(Tutor.user_id == user.id))
        if tutor is not None:
            return tutor.public_id, tutor.display_name
    elif user.role == "parent":
        parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
        if parent is not None:
            return parent.public_id, parent.display_name
    return None, None


def _open_invoices_stmt():
    return select(Invoice).where(
        Invoice.status != "cancelled",
        Invoice.total_paise > Invoice.paid_paise,
    )


def _outstanding(invoice: Invoice) -> int:
    return invoice.total_paise - invoice.paid_paise


def _is_overdue(invoice: Invoice, today: date) -> bool:
    return invoice.status == "overdue" or invoice.due_date < today


def _require_password(user: User, password: str) -> None:
    if not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PASSWORD_INCORRECT_DETAIL)


def _latest_requested(db: Session, user: User) -> AccountDeletionRequest | None:
    return db.scalar(
        select(AccountDeletionRequest)
        .where(
            AccountDeletionRequest.user_id == user.id,
            AccountDeletionRequest.status == "requested",
        )
        .order_by(AccountDeletionRequest.created_at.desc())
        .limit(1)
    )


def _tutor_business(db: Session, tutor: Tutor) -> Business | None:
    return db.scalar(select(Business).where(Business.tutor_id == tutor.id))


@router.get("/settings")
def get_settings_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    public_id, display_name = _identity(db, user)
    return {
        "phone": user.phone,
        "role": user.role,
        "display_name": display_name,
        "public_id": public_id,
        "notification_preferences": {"email": False, "in_app": True},
    }


@router.put("/settings")
def update_settings_profile(
    body: SettingsUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if user.role == "tutor":
        profile = _tutor_row(db, user)
    else:
        profile = _parent_row(db, user)
    profile.display_name = body.display_name
    db.commit()
    return {"status": "ok", "display_name": profile.display_name}


@router.post("/logout")
def logout(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    db.add(
        ActivityLog(
            user_id=user.id,
            action="logout",
            entity="user",
            entity_id=str(user.id),
        )
    )
    db.commit()
    return {"status": "ok"}


def _tutor_preview(db: Session, user: User) -> dict:
    tutor = _tutor_row(db, user)
    today = date.today()
    business = _tutor_business(db, tutor)

    open_invoices: list[Invoice] = []
    pending_claims = 0
    pending_enrollments = 0
    unpaid_expenses: list[Expense] = []
    if business is not None:
        open_invoices = list(
            db.scalars(_open_invoices_stmt().where(Invoice.business_id == business.id)).all()
        )
        pending_claims = db.scalar(
            select(func.count(PaymentClaim.id)).where(
                PaymentClaim.business_id == business.id,
                PaymentClaim.status.in_(OPEN_CLAIM_STATUSES),
            )
        ) or 0
        pending_enrollments = db.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.business_id == business.id,
                Enrollment.status == "requested",
            )
        ) or 0
        unpaid_expenses = list(
            db.scalars(
                select(Expense).where(
                    Expense.business_id == business.id,
                    Expense.status == "unpaid",
                )
            ).all()
        )

    return {
        "role": "tutor",
        "unpaid_invoice_count": len(open_invoices),
        "outstanding_paise": sum(_outstanding(inv) for inv in open_invoices),
        "parents_with_unpaid_fees": len({inv.parent_id for inv in open_invoices if inv.parent_id is not None}),
        "overdue_invoice_count": sum(1 for inv in open_invoices if _is_overdue(inv, today)),
        "pending_claims_count": pending_claims,
        "pending_enrollments_count": pending_enrollments,
        "unpaid_expenses_count": len(unpaid_expenses),
        "unpaid_expenses_paise": sum(exp.amount_paise for exp in unpaid_expenses),
        "retention_notice": RETENTION_NOTICE,
    }


def _parent_preview(db: Session, user: User) -> dict:
    parent = _parent_row(db, user)
    today = date.today()
    child_ids = select(ParentStudentLink.student_id).where(ParentStudentLink.parent_id == parent.id)

    children_count = db.scalar(
        select(func.count(Student.id)).where(
            Student.id.in_(child_ids),
            Student.deleted_at.is_(None),
        )
    ) or 0
    open_invoices = list(db.scalars(_open_invoices_stmt().where(Invoice.parent_id == parent.id)).all())
    pending_claims = db.scalar(
        select(func.count(PaymentClaim.id)).where(
            PaymentClaim.parent_id == parent.id,
            PaymentClaim.status.in_(OPEN_CLAIM_STATUSES),
        )
    ) or 0
    requested_enrollments = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.parent_id == parent.id,
            Enrollment.status == "requested",
        )
    ) or 0

    return {
        "role": "parent",
        "children_count": children_count,
        "outstanding_paise": sum(_outstanding(inv) for inv in open_invoices),
        "overdue_count": sum(1 for inv in open_invoices if _is_overdue(inv, today)),
        "pending_claims_count": pending_claims,
        "pending_enrollments_count": requested_enrollments,
        "retention_notice": RETENTION_NOTICE,
    }


@router.get("/deletion-preview")
def deletion_preview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if user.role == "tutor":
        return _tutor_preview(db, user)
    return _parent_preview(db, user)


@router.post("/deletion-request", status_code=status.HTTP_201_CREATED)
def request_deletion(
    body: PasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    _require_password(user, body.password)
    request = AccountDeletionRequest(user_id=user.id, status="requested")
    db.add(request)
    db.commit()
    db.refresh(request)
    return {"status": "requested", "request_id": str(request.id)}


@router.post("/deletion-request/confirm")
def confirm_deletion(
    body: DeletionConfirmIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if body.confirmation_phrase != CONFIRMATION_PHRASE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Confirmation phrase must be exactly '{CONFIRMATION_PHRASE}'",
        )
    _require_password(user, body.password)

    request = _latest_requested(db, user)
    if request is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=NO_PENDING_REQUEST_DETAIL)

    has_outstanding_business = False
    if user.role == "tutor":
        tutor = _tutor_row(db, user)
        business = _tutor_business(db, tutor)
        if business is not None:
            has_outstanding_business = db.scalar(
                select(func.count(Invoice.id)).where(
                    Invoice.business_id == business.id,
                    Invoice.status != "cancelled",
                    Invoice.total_paise > Invoice.paid_paise,
                )
            ) > 0

    request.status = "confirmed"
    request.confirmed_at = datetime.now(timezone.utc)
    user.status = "deactivated"
    db.add(
        AccountStatusHistory(
            user_id=user.id,
            from_status="active",
            to_status="deactivated",
            reason="self_requested_deletion",
        )
    )
    db.add(
        ActivityLog(
            user_id=user.id,
            action="account_deletion_confirmed",
            entity="user",
            entity_id=str(user.id),
        )
    )
    db.commit()

    message = (
        "Your account is deactivated. Financial records have been retained as required. "
        "It is not permanently erased."
    )
    if has_outstanding_business:
        message += " Outstanding business records remain on file."
    return {"status": "deactivated", "message": message}


@router.post("/deletion-request/cancel")
def cancel_deletion(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    request = _latest_requested(db, user)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NO_PENDING_REQUEST_DETAIL)
    request.status = "cancelled"
    db.commit()
    return {"status": "cancelled", "request_id": str(request.id)}
