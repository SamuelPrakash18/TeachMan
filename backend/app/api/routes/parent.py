import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_parent
from app.db.session import get_db
from app.models.finance import Invoice, PaymentClaim
from app.models.student import ParentStudentLink, Student
from app.models.teaching import Enrollment
from app.models.user import Parent, User
from app.schemas.parent import ChildIn, ChildOut, ChildUpdate, ParentDashboardOut

router = APIRouter(prefix="/api/parent", tags=["parent"])

PARENT_PROFILE_MISSING_DETAIL = "Parent profile not found"
CHILD_NOT_FOUND_DETAIL = "Child not found"
OPEN_CLAIM_STATUSES = ("pending", "under_review")


def _parent_for(db: Session, user: User) -> Parent:
    parent = db.scalar(select(Parent).where(Parent.user_id == user.id))
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PARENT_PROFILE_MISSING_DETAIL)
    return parent


def _next_student_public_id(db: Session) -> str:
    prefix = "STU-"
    current_max = db.scalar(select(func.max(Student.public_id)))
    next_number = (int(current_max[len(prefix):]) if current_max else 0) + 1
    return f"{prefix}{next_number:06d}"


def _linked_child_ids(parent: Parent):
    return select(ParentStudentLink.student_id).where(ParentStudentLink.parent_id == parent.id)


def _linked_children_stmt(parent: Parent):
    return (
        select(Student)
        .where(Student.id.in_(_linked_child_ids(parent)), Student.deleted_at.is_(None))
        .order_by(Student.name)
    )


def _open_invoices_stmt(parent: Parent):
    return select(Invoice).where(
        Invoice.parent_id == parent.id,
        Invoice.student_id.in_(_linked_child_ids(parent)),
        Invoice.status != "cancelled",
        Invoice.total_paise > Invoice.paid_paise,
    )


@router.get("/children", response_model=list[ChildOut])
def list_children(
    user: User = Depends(require_parent),
    db: Session = Depends(get_db),
) -> list[ChildOut]:
    parent = _parent_for(db, user)
    children = db.scalars(_linked_children_stmt(parent)).all()
    return [ChildOut.model_validate(child) for child in children]


@router.post("/children", response_model=ChildOut, status_code=status.HTTP_201_CREATED)
def add_child(
    body: ChildIn,
    user: User = Depends(require_parent),
    db: Session = Depends(get_db),
) -> ChildOut:
    parent = _parent_for(db, user)
    student = Student(
        public_id=_next_student_public_id(db),
        business_id=None,
        name=body.name,
        grade=body.grade,
        address=body.address or "",
        enrolled_on=date.today(),
    )
    db.add(student)
    db.flush()
    db.add(ParentStudentLink(parent_id=parent.id, student_id=student.id))
    db.commit()
    db.refresh(student)
    return ChildOut.model_validate(student)


@router.put("/children/{child_id}", response_model=ChildOut)
def update_child(
    child_id: uuid.UUID,
    body: ChildUpdate,
    user: User = Depends(require_parent),
    db: Session = Depends(get_db),
) -> ChildOut:
    parent = _parent_for(db, user)
    child = db.scalar(_linked_children_stmt(parent).where(Student.id == child_id))
    if child is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CHILD_NOT_FOUND_DETAIL)

    changes = body.model_dump(exclude_unset=True)
    for field in ("name", "grade"):
        if field in changes and changes[field] is not None:
            setattr(child, field, changes[field])
    if "address" in changes:
        child.address = changes["address"] or ""
    db.commit()
    db.refresh(child)
    return ChildOut.model_validate(child)


@router.get("/dashboard", response_model=ParentDashboardOut)
def dashboard(
    user: User = Depends(require_parent),
    db: Session = Depends(get_db),
) -> ParentDashboardOut:
    parent = _parent_for(db, user)
    today = date.today()

    children = db.scalars(_linked_children_stmt(parent)).all()
    open_invoices = db.scalars(_open_invoices_stmt(parent)).all()

    outstanding = sum(inv.total_paise - inv.paid_paise for inv in open_invoices)
    overdue = sum(1 for inv in open_invoices if inv.status == "overdue" or inv.due_date < today)
    next_due = min((inv.due_date for inv in open_invoices), default=None)

    pending_claims = db.scalar(
        select(func.count(PaymentClaim.id))
        .join(Invoice, Invoice.id == PaymentClaim.invoice_id)
        .where(
            PaymentClaim.parent_id == parent.id,
            Invoice.student_id.in_(_linked_child_ids(parent)),
            PaymentClaim.status.in_(OPEN_CLAIM_STATUSES),
        )
    ) or 0

    pending_enrollments = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.parent_id == parent.id,
            Enrollment.student_id.in_(_linked_child_ids(parent)),
            Enrollment.status == "requested",
        )
    ) or 0

    return ParentDashboardOut(
        parent_name=parent.display_name,
        children_count=len(children),
        outstanding_paise=outstanding,
        overdue_count=overdue,
        pending_claims_count=pending_claims,
        pending_enrollments_count=pending_enrollments,
        next_due_date=next_due,
    )

