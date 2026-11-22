import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_parent, require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.student import ParentStudentLink, Student
from app.models.system import Notification
from app.models.teaching import Batch, Enrollment
from app.models.user import Parent, Tutor, User
from app.schemas.teaching import EnrollmentOut, EnrollmentRequestIn
from app.services.enrollment_service import on_enrollment_approved

router = APIRouter(prefix="/api/enrollments", tags=["enrollments"])

APPROVED = "approved"
REQUESTED = "requested"
OPEN_STATUSES = (REQUESTED, APPROVED)
ENROLLMENT_NOT_FOUND_DETAIL = "Enrollment not found"


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


def _approved_count(db: Session, batch_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.batch_id == batch_id,
            Enrollment.status == APPROVED,
        )
    ) or 0


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


def _to_out(db: Session, enrollment: Enrollment) -> EnrollmentOut:
    student = db.get(Student, enrollment.student_id)
    batch = db.get(Batch, enrollment.batch_id)
    return EnrollmentOut(
        id=enrollment.id,
        student_id=enrollment.student_id,
        student_name=student.name if student else "",
        batch_id=enrollment.batch_id,
        batch_name=batch.name if batch else "",
        status=enrollment.status,
        requested_at=enrollment.requested_at,
        decided_at=enrollment.decided_at,
    )


def _load_owned_enrollment(db: Session, business: Business, enrollment_id: uuid.UUID) -> Enrollment:
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.id == enrollment_id,
            Enrollment.business_id == business.id,
        )
    )
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ENROLLMENT_NOT_FOUND_DETAIL)
    return enrollment


@router.post("/request", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def request_enrollment(
    body: EnrollmentRequestIn,
    user: User = Depends(require_parent),
    db: Session = Depends(get_db),
) -> EnrollmentOut:
    parent = _caller_parent(db, user)

    linked = db.scalar(
        select(ParentStudentLink.id).where(
            ParentStudentLink.parent_id == parent.id,
            ParentStudentLink.student_id == body.student_id,
        )
    )
    if linked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    student = db.scalar(
        select(Student).where(Student.id == body.student_id, Student.deleted_at.is_(None))
    )
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    batch = db.scalar(select(Batch).where(Batch.id == body.batch_id))
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    if batch.status != "active":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Batch is not open for enrollment")

    if student.business_id is not None and student.business_id != batch.business_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is registered with a different tuition",
        )

    open_exists = db.scalar(
        select(Enrollment.id).where(
            Enrollment.student_id == student.id,
            Enrollment.batch_id == batch.id,
            Enrollment.status.in_(OPEN_STATUSES),
        )
    )
    if open_exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An open enrollment already exists for this student and batch",
        )

    if _approved_count(db, batch.id) >= batch.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No seats left in this batch")

    try:
        # Attach an unassigned student to this tuition so the tutor can see them.
        if student.business_id is None:
            student.business_id = batch.business_id

        enrollment = Enrollment(
            business_id=batch.business_id,
            student_id=student.id,
            batch_id=batch.id,
            parent_id=parent.id,
            status=REQUESTED,
        )
        db.add(enrollment)
        _notify(
            db,
            _tutor_user_id(db, batch.business_id),
            "New enrollment request",
            f"{student.name} has requested to join {batch.name}.",
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An open enrollment already exists for this student and batch",
        )

    db.refresh(enrollment)
    return _to_out(db, enrollment)


@router.get("", response_model=list[EnrollmentOut])
def list_enrollments(
    status_filter: str | None = Query(default=None, alias="status", max_length=10),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[EnrollmentOut]:
    stmt = select(Enrollment)

    if user.role == "tutor":
        business = _caller_business(db, user)
        stmt = stmt.where(Enrollment.business_id == business.id)
    elif user.role == "parent":
        parent = _caller_parent(db, user)
        linked_students = select(ParentStudentLink.student_id).where(
            ParentStudentLink.parent_id == parent.id
        )
        stmt = stmt.where(Enrollment.student_id.in_(linked_students))
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if status_filter:
        stmt = stmt.where(Enrollment.status == status_filter)

    enrollments = db.scalars(stmt.order_by(Enrollment.requested_at.desc())).all()
    return [_to_out(db, e) for e in enrollments]


@router.post("/{enrollment_id}/approve", response_model=EnrollmentOut)
def approve_enrollment(
    enrollment_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> EnrollmentOut:
    business = _caller_business(db, user)
    enrollment = _load_owned_enrollment(db, business, enrollment_id)

    # Lock the batch row so concurrent approvals cannot overfill it.
    batch = db.scalar(
        select(Batch)
        .where(Batch.id == enrollment.batch_id, Batch.business_id == business.id)
        .with_for_update()
    )
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

    db.refresh(enrollment)
    if enrollment.status != REQUESTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Enrollment is not awaiting a decision")

    if _approved_count(db, batch.id) >= batch.capacity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No seats left in this batch")

    student = db.get(Student, enrollment.student_id)
    enrollment.status = APPROVED
    enrollment.decided_at = datetime.now(timezone.utc)
    on_enrollment_approved(db, enrollment)

    _notify(
        db,
        _parent_user_id(db, enrollment.parent_id),
        "Enrollment approved",
        f"{student.name if student else 'Your child'} has been approved for {batch.name}.",
    )
    db.commit()
    db.refresh(enrollment)
    return _to_out(db, enrollment)


@router.post("/{enrollment_id}/reject", response_model=EnrollmentOut)
def reject_enrollment(
    enrollment_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> EnrollmentOut:
    business = _caller_business(db, user)
    enrollment = _load_owned_enrollment(db, business, enrollment_id)

    if enrollment.status != REQUESTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Enrollment is not awaiting a decision")

    student = db.get(Student, enrollment.student_id)
    batch = db.get(Batch, enrollment.batch_id)
    enrollment.status = "rejected"
    enrollment.decided_at = datetime.now(timezone.utc)

    _notify(
        db,
        _parent_user_id(db, enrollment.parent_id),
        "Enrollment request declined",
        f"The request for {student.name if student else 'your child'} to join "
        f"{batch.name if batch else 'the batch'} was declined.",
    )
    db.commit()
    db.refresh(enrollment)
    return _to_out(db, enrollment)
