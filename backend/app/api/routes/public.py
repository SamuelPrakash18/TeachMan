import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.business import Business, BusinessAddress
from app.models.teaching import Batch, BatchSchedule, Course, Enrollment
from app.models.user import Tutor

router = APIRouter(prefix="/api/public", tags=["public"])


class PublicTutorOut(BaseModel):
    id: uuid.UUID
    tuition_name: str
    display_name: str
    district: str
    subjects: list[str]
    grades: list[str]
    teaching_mode: str


class PublicBatchOut(BaseModel):
    id: uuid.UUID
    name: str
    tutor_name: str
    course_label: str
    monthly_fee_paise: int
    seats_left: int
    teaching_mode: str
    schedules: list[str]


@router.get("/tutors", response_model=list[PublicTutorOut])
def list_public_tutors(
    subject: str | None = Query(default=None),
    grade: str | None = Query(default=None),
    district: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PublicTutorOut]:
    rows = db.execute(
        select(Tutor, Business, BusinessAddress)
        .join(Business, Business.tutor_id == Tutor.id)
        .join(BusinessAddress, BusinessAddress.business_id == Business.id)
        .order_by(Business.tuition_name)
    ).all()
    subject_filter = subject.strip().casefold() if subject else None
    grade_filter = grade.strip().casefold() if grade else None
    district_filter = district.strip().casefold() if district else None
    results: list[PublicTutorOut] = []
    for tutor, business, address in rows:
        if subject_filter and not any(subject_filter == value.casefold() for value in business.subjects):
            continue
        if grade_filter and not any(grade_filter == value.casefold() for value in business.grades):
            continue
        if district_filter and district_filter not in address.district.casefold():
            continue
        results.append(
            PublicTutorOut(
                id=tutor.id,
                tuition_name=business.tuition_name,
                display_name=tutor.display_name,
                district=address.district,
                subjects=list(business.subjects),
                grades=list(business.grades),
                teaching_mode=business.teaching_mode,
            )
        )
    return results


@router.get("/batches", response_model=list[PublicBatchOut])
def list_public_batches(db: Session = Depends(get_db)) -> list[PublicBatchOut]:
    rows = db.execute(
        select(Batch, Tutor, Course)
        .join(Business, Business.id == Batch.business_id)
        .join(Tutor, Tutor.id == Business.tutor_id)
        .join(Course, Course.id == Batch.course_id)
        .where(Batch.status == "active")
        .order_by(Batch.name)
    ).all()
    results: list[PublicBatchOut] = []
    for batch, tutor, course in rows:
        enrolled_count = db.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.batch_id == batch.id,
                Enrollment.status == "approved",
            )
        ) or 0
        seats_left = max(batch.capacity - int(enrolled_count), 0)
        if seats_left == 0:
            continue
        schedules = db.scalars(
            select(BatchSchedule)
            .where(BatchSchedule.batch_id == batch.id)
            .order_by(BatchSchedule.weekday, BatchSchedule.start_time)
        ).all()
        results.append(
            PublicBatchOut(
                id=batch.id,
                name=batch.name,
                tutor_name=tutor.display_name,
                course_label=f"{course.subject} - {course.grade}",
                monthly_fee_paise=batch.monthly_fee_paise,
                seats_left=seats_left,
                teaching_mode=batch.teaching_mode,
                schedules=[
                    f"{schedule.weekday} {schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                    for schedule in schedules
                ],
            )
        )
    return results
