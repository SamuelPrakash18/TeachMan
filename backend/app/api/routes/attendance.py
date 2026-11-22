import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.student import ParentStudentLink, Student
from app.models.teaching import Attendance, Batch, ClassSession, Enrollment
from app.models.user import Parent, Tutor, User
from app.schemas.learning import (
    AttendanceMarkIn,
    AttendanceOut,
    AttendanceRecordOut,
    ClassSessionIn,
    ClassSessionOut,
    ClassSessionStatusIn,
    StudentAttendanceRecordOut,
    StudentAttendanceSummaryOut,
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])

APPROVED = "approved"
SESSION_NOT_FOUND_DETAIL = "Class session not found"
BATCH_NOT_FOUND_DETAIL = "Batch not found"
STUDENT_NOT_FOUND_DETAIL = "Student not found"


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


def _load_session(db: Session, business: Business, session_id: uuid.UUID) -> ClassSession:
    session = db.scalar(
        select(ClassSession)
        .join(Batch, Batch.id == ClassSession.batch_id)
        .where(ClassSession.id == session_id, Batch.business_id == business.id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SESSION_NOT_FOUND_DETAIL)
    return session


def _tutor_can_see_student(db: Session, business: Business, student_id: uuid.UUID) -> bool:
    owned = db.scalar(
        select(Student.id).where(Student.id == student_id, Student.business_id == business.id)
    )
    if owned is not None:
        return True
    enrolled = db.scalar(
        select(Enrollment.id).where(
            Enrollment.student_id == student_id,
            Enrollment.business_id == business.id,
            Enrollment.status == APPROVED,
        )
    )
    return enrolled is not None


def _session_out(db: Session, session: ClassSession) -> ClassSessionOut:
    batch = db.get(Batch, session.batch_id)
    return ClassSessionOut(
        id=session.id,
        batch_id=session.batch_id,
        batch_name=batch.name if batch else "",
        session_date=session.session_date,
        status=session.status,
    )


def _attendance_out(db: Session, session: ClassSession) -> AttendanceOut:
    batch = db.get(Batch, session.batch_id)
    rows = db.execute(
        select(Attendance.student_id, Student.name, Attendance.status)
        .select_from(Attendance)
        .join(Student, Student.id == Attendance.student_id)
        .where(Attendance.session_id == session.id)
        .order_by(Student.name)
    ).all()
    return AttendanceOut(
        session_id=session.id,
        session_date=session.session_date,
        batch_name=batch.name if batch else "",
        records=[
            AttendanceRecordOut(student_id=student_id, student_name=name, status=status_value)
            for student_id, name, status_value in rows
        ],
    )


@router.post("/sessions", response_model=ClassSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    body: ClassSessionIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> ClassSessionOut:
    business = _caller_business(db, user)
    batch = db.scalar(
        select(Batch).where(Batch.id == body.batch_id, Batch.business_id == business.id)
    )
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BATCH_NOT_FOUND_DETAIL)

    existing = db.scalar(
        select(ClassSession.id).where(
            ClassSession.batch_id == batch.id,
            ClassSession.session_date == body.session_date,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A session already exists for this batch and date",
        )

    session = ClassSession(
        batch_id=batch.id,
        session_date=body.session_date,
        status=body.status,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return _session_out(db, session)


@router.get("/sessions", response_model=list[ClassSessionOut])
def list_sessions(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> list[ClassSessionOut]:
    business = _caller_business(db, user)
    stmt = (
        select(ClassSession)
        .join(Batch, Batch.id == ClassSession.batch_id)
        .where(Batch.business_id == business.id)
    )
    if from_date is not None:
        stmt = stmt.where(ClassSession.session_date >= from_date)
    if to_date is not None:
        stmt = stmt.where(ClassSession.session_date <= to_date)
    sessions = db.scalars(stmt.order_by(ClassSession.session_date, ClassSession.id)).all()
    return [_session_out(db, s) for s in sessions]


@router.put("/sessions/{session_id}/status", response_model=ClassSessionOut)
def update_session_status(
    session_id: uuid.UUID,
    body: ClassSessionStatusIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> ClassSessionOut:
    business = _caller_business(db, user)
    session = _load_session(db, business, session_id)
    session.status = body.status
    db.commit()
    db.refresh(session)
    return _session_out(db, session)


@router.post("/mark", response_model=AttendanceOut)
def mark_attendance(
    body: AttendanceMarkIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> AttendanceOut:
    business = _caller_business(db, user)
    session = _load_session(db, business, body.session_id)

    desired: dict[uuid.UUID, str] = {}
    for record in body.records:
        desired[record.student_id] = record.status

    if desired:
        approved_ids = set(
            db.scalars(
                select(Enrollment.student_id).where(
                    Enrollment.business_id == business.id,
                    Enrollment.batch_id == session.batch_id,
                    Enrollment.status == APPROVED,
                )
            ).all()
        )
        if any(student_id not in approved_ids for student_id in desired):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Every student must have an approved enrollment in this batch",
            )

        existing = {
            row.student_id: row
            for row in db.scalars(
                select(Attendance).where(
                    Attendance.session_id == session.id,
                    Attendance.student_id.in_(list(desired.keys())),
                )
            ).all()
        }
        for student_id, status_value in desired.items():
            row = existing.get(student_id)
            if row is None:
                db.add(
                    Attendance(
                        session_id=session.id,
                        student_id=student_id,
                        status=status_value,
                    )
                )
            else:
                row.status = status_value

    db.commit()
    return _attendance_out(db, session)


@router.get("/sessions/{session_id}", response_model=AttendanceOut)
def get_session_attendance(
    session_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> AttendanceOut:
    business = _caller_business(db, user)
    session = _load_session(db, business, session_id)
    return _attendance_out(db, session)


@router.get("/students/{student_id}", response_model=StudentAttendanceSummaryOut)
def get_student_attendance(
    student_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentAttendanceSummaryOut:
    stmt = (
        select(Attendance.status, ClassSession.session_date, Batch.name)
        .select_from(Attendance)
        .join(ClassSession, ClassSession.id == Attendance.session_id)
        .join(Batch, Batch.id == ClassSession.batch_id)
        .where(Attendance.student_id == student_id)
    )

    if user.role == "tutor":
        business = _caller_business(db, user)
        if not _tutor_can_see_student(db, business, student_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND_DETAIL)
        stmt = stmt.where(Batch.business_id == business.id)
    elif user.role == "parent":
        parent = _caller_parent(db, user)
        linked = db.scalar(
            select(ParentStudentLink.id).where(
                ParentStudentLink.parent_id == parent.id,
                ParentStudentLink.student_id == student_id,
            )
        )
        if linked is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND_DETAIL)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    rows = db.execute(stmt.order_by(ClassSession.session_date, Batch.name)).all()

    total = len(rows)
    present = sum(1 for row in rows if row.status == "present")
    absent = sum(1 for row in rows if row.status == "absent")
    excused = sum(1 for row in rows if row.status == "excused")
    percent_present = (present * 100 // total) if total else 0

    return StudentAttendanceSummaryOut(
        total=total,
        present=present,
        absent=absent,
        excused=excused,
        percent_present=percent_present,
        records=[
            StudentAttendanceRecordOut(session_date=row.session_date, batch_name=row.name, status=row.status)
            for row in rows
        ],
    )
