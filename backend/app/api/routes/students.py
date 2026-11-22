import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.student import ParentStudentLink, Student
from app.models.teaching import Enrollment
from app.models.user import Parent, Tutor, User
from app.schemas.student import StudentIn, StudentOut, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])

OPEN_ENROLLMENT_STATUSES = ("requested", "approved")
NOT_FOUND_DETAIL = "Student not found"
PUBLIC_ID_CONFLICT_DETAIL = "Student registration conflicts with an existing record"


def _caller_business(db: Session, user: User) -> Business:
    business = db.scalar(
        select(Business).join(Tutor, Tutor.id == Business.tutor_id).where(Tutor.user_id == user.id)
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


def _next_public_id(db: Session, column, prefix: str) -> str:
    current_max = db.scalar(select(func.max(column)))
    next_number = (int(current_max[len(prefix):]) if current_max else 0) + 1
    return f"{prefix}{next_number:06d}"


def _load_student(db: Session, business: Business, student_id: uuid.UUID) -> Student:
    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.business_id == business.id,
            Student.deleted_at.is_(None),
        )
    )
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)
    return student


def _parent_contacts(db: Session, student_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[str, str]]:
    if not student_ids:
        return {}
    rows = db.execute(
        select(ParentStudentLink.student_id, Parent.display_name, User.phone)
        .join(Parent, Parent.id == ParentStudentLink.parent_id)
        .join(User, User.id == Parent.user_id)
        .where(ParentStudentLink.student_id.in_(student_ids))
    ).all()
    contacts: dict[uuid.UUID, tuple[str, str]] = {}
    for student_id, parent_name, parent_phone in rows:
        contacts.setdefault(student_id, (parent_name, parent_phone))
    return contacts


def _to_out(student: Student, contact: tuple[str, str] | None) -> StudentOut:
    parent_name, parent_phone = contact if contact is not None else (None, None)
    return StudentOut(
        id=student.id,
        public_id=student.public_id,
        name=student.name,
        grade=student.grade,
        address=student.address,
        enrolled_on=student.enrolled_on,
        parent_name=parent_name,
        parent_phone=parent_phone,
    )


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("", response_model=list[StudentOut])
def list_students(
    q: str | None = Query(default=None, max_length=120),
    grade: str | None = Query(default=None, max_length=20),
    batch_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> list[StudentOut]:
    business = _caller_business(db, user)
    stmt = select(Student).where(
        Student.business_id == business.id,
        Student.deleted_at.is_(None),
    )
    if q and q.strip():
        stmt = stmt.where(Student.name.ilike(f"%{_escape_like(q.strip())}%", escape="\\"))
    if grade:
        stmt = stmt.where(Student.grade == grade)
    if batch_id is not None:
        enrolled_ids = select(Enrollment.student_id).where(
            Enrollment.business_id == business.id,
            Enrollment.batch_id == batch_id,
            Enrollment.status.in_(OPEN_ENROLLMENT_STATUSES),
        )
        stmt = stmt.where(Student.id.in_(enrolled_ids))

    students = list(db.scalars(stmt.order_by(Student.name, Student.public_id)).all())
    contacts = _parent_contacts(db, [s.id for s in students])
    return [_to_out(s, contacts.get(s.id)) for s in students]


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(
    body: StudentIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> StudentOut:
    business = _caller_business(db, user)
    try:
        student = Student(
            public_id=_next_public_id(db, Student.public_id, "STU-"),
            business_id=business.id,
            name=body.name,
            grade=body.grade,
            address=body.address or "",
            enrolled_on=date.today(),
        )
        db.add(student)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=PUBLIC_ID_CONFLICT_DETAIL)

    # A newly created student has no linked parent yet.
    return _to_out(student, None)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(
    student_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> StudentOut:
    business = _caller_business(db, user)
    student = _load_student(db, business, student_id)
    contacts = _parent_contacts(db, [student.id])
    return _to_out(student, contacts.get(student.id))


@router.put("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> StudentOut:
    business = _caller_business(db, user)
    student = _load_student(db, business, student_id)
    changes = body.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if field == "address":
            value = value or ""
        setattr(student, field, value)

    db.commit()
    contacts = _parent_contacts(db, [student.id])
    return _to_out(student, contacts.get(student.id))
