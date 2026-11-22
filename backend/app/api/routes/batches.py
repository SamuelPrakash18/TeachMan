import uuid
from datetime import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.teaching import Batch, BatchSchedule, Course, Enrollment
from app.models.user import Tutor, User
from app.schemas.teaching import BatchIn, BatchOut, BatchUpdate, ScheduleIn, ScheduleOut

router = APIRouter(prefix="/api/batches", tags=["batches"])

APPROVED = "approved"
BATCH_NOT_FOUND_DETAIL = "Batch not found"
COURSE_NOT_FOUND_DETAIL = "Course not found"
CAPACITY_CONFLICT_DETAIL = "Capacity cannot be lower than the number of approved enrollments"


def _caller_business(db: Session, user: User) -> Business:
    business = db.scalar(
        select(Business).join(Tutor, Tutor.id == Business.tutor_id).where(Tutor.user_id == user.id)
    )
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business


def _load_course(db: Session, business: Business, course_id: uuid.UUID) -> Course:
    course = db.scalar(
        select(Course).where(Course.id == course_id, Course.business_id == business.id)
    )
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=COURSE_NOT_FOUND_DETAIL)
    return course


def _load_batch(
    db: Session, business: Business, batch_id: uuid.UUID, lock: bool = False
) -> Batch:
    stmt = select(Batch).where(Batch.id == batch_id, Batch.business_id == business.id)
    if lock:
        stmt = stmt.with_for_update()
    batch = db.scalar(stmt)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=BATCH_NOT_FOUND_DETAIL)
    return batch


def _approved_count(db: Session, batch_id: uuid.UUID) -> int:
    return db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.batch_id == batch_id,
            Enrollment.status == APPROVED,
        )
    ) or 0


def _schedule_rows(batch_id: uuid.UUID, schedules: list[ScheduleIn]) -> list[BatchSchedule]:
    return [
        BatchSchedule(
            batch_id=batch_id,
            weekday=s.weekday,
            start_time=time.fromisoformat(s.start_time),
            end_time=time.fromisoformat(s.end_time),
            location=s.location,
            meeting_link=s.meeting_link,
        )
        for s in schedules
    ]


def _to_outs(db: Session, batches: list[Batch]) -> list[BatchOut]:
    if not batches:
        return []
    batch_ids = [b.id for b in batches]
    course_ids = {b.course_id for b in batches}

    courses = {
        c.id: c
        for c in db.scalars(select(Course).where(Course.id.in_(course_ids))).all()
    }
    counts = dict(
        db.execute(
            select(Enrollment.batch_id, func.count(Enrollment.id))
            .where(Enrollment.batch_id.in_(batch_ids), Enrollment.status == APPROVED)
            .group_by(Enrollment.batch_id)
        ).all()
    )
    schedules: dict[uuid.UUID, list[BatchSchedule]] = {}
    for row in db.scalars(
        select(BatchSchedule)
        .where(BatchSchedule.batch_id.in_(batch_ids))
        .order_by(BatchSchedule.weekday, BatchSchedule.start_time)
    ).all():
        schedules.setdefault(row.batch_id, []).append(row)

    outs: list[BatchOut] = []
    for batch in batches:
        course = courses[batch.course_id]
        enrolled = counts.get(batch.id, 0)
        outs.append(
            BatchOut(
                id=batch.id,
                course_id=batch.course_id,
                course_label=f"{course.subject} - {course.grade}",
                name=batch.name,
                monthly_fee_paise=batch.monthly_fee_paise,
                capacity=batch.capacity,
                enrolled_count=enrolled,
                seats_left=max(batch.capacity - enrolled, 0),
                teaching_mode=batch.teaching_mode,
                status=batch.status,
                schedules=[
                    ScheduleOut(
                        weekday=s.weekday,
                        start_time=s.start_time.strftime("%H:%M"),
                        end_time=s.end_time.strftime("%H:%M"),
                        location=s.location,
                        meeting_link=s.meeting_link,
                    )
                    for s in schedules.get(batch.id, [])
                ],
            )
        )
    return outs


@router.get("", response_model=list[BatchOut])
def list_batches(
    course_id: uuid.UUID | None = Query(default=None),
    batch_status: Literal["active", "paused", "closed"] | None = Query(default=None, alias="status"),
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> list[BatchOut]:
    business = _caller_business(db, user)
    stmt = select(Batch).where(Batch.business_id == business.id)
    if course_id is not None:
        stmt = stmt.where(Batch.course_id == course_id)
    if batch_status is not None:
        stmt = stmt.where(Batch.status == batch_status)
    batches = list(db.scalars(stmt.order_by(Batch.name)).all())
    return _to_outs(db, batches)


@router.post("", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    body: BatchIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> BatchOut:
    business = _caller_business(db, user)
    course = _load_course(db, business, body.course_id)

    batch = Batch(
        business_id=business.id,
        course_id=course.id,
        name=body.name,
        monthly_fee_paise=body.monthly_fee_paise,
        capacity=body.capacity,
        teaching_mode=body.teaching_mode,
        status=body.status,
    )
    db.add(batch)
    db.flush()
    db.add_all(_schedule_rows(batch.id, body.schedules))
    db.commit()
    return _to_outs(db, [batch])[0]


@router.get("/{batch_id}", response_model=BatchOut)
def get_batch(
    batch_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> BatchOut:
    business = _caller_business(db, user)
    batch = _load_batch(db, business, batch_id)
    return _to_outs(db, [batch])[0]


@router.put("/{batch_id}", response_model=BatchOut)
def update_batch(
    batch_id: uuid.UUID,
    body: BatchUpdate,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> BatchOut:
    business = _caller_business(db, user)
    # Lock the batch row so capacity checks and approvals cannot race.
    batch = _load_batch(db, business, batch_id, lock=True)
    changes = body.model_dump(exclude_unset=True)

    if "course_id" in changes:
        course = _load_course(db, business, body.course_id)
        batch.course_id = course.id

    if "capacity" in changes and body.capacity < _approved_count(db, batch.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=CAPACITY_CONFLICT_DETAIL)

    for field in ("name", "monthly_fee_paise", "capacity", "teaching_mode", "status"):
        if field in changes:
            setattr(batch, field, getattr(body, field))

    if "schedules" in changes:
        db.execute(delete(BatchSchedule).where(BatchSchedule.batch_id == batch.id))
        db.add_all(_schedule_rows(batch.id, body.schedules))

    db.commit()
    return _to_outs(db, [batch])[0]


@router.delete("/{batch_id}", response_model=BatchOut)
def close_batch(
    batch_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> BatchOut:
    # Batches are never hard-deleted: DELETE only sets status = 'closed'.
    business = _caller_business(db, user)
    batch = _load_batch(db, business, batch_id)
    batch.status = "closed"
    db.commit()
    return _to_outs(db, [batch])[0]
