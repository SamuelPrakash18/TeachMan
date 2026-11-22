import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.teaching import Batch, Course
from app.models.user import Tutor, User
from app.schemas.teaching import CourseIn, CourseOut, CourseUpdate

router = APIRouter(prefix="/api/courses", tags=["courses"])

NOT_FOUND_DETAIL = "Course not found"
COURSE_CONFLICT_DETAIL = "A course for this subject and grade already exists"


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND_DETAIL)
    return course


def _batch_counts(db: Session, course_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not course_ids:
        return {}
    rows = db.execute(
        select(Batch.course_id, func.count(Batch.id))
        .where(Batch.course_id.in_(course_ids))
        .group_by(Batch.course_id)
    ).all()
    return {course_id: count for course_id, count in rows}


def _to_out(course: Course, batch_count: int) -> CourseOut:
    return CourseOut(
        id=course.id,
        subject=course.subject,
        grade=course.grade,
        is_active=course.is_active,
        batch_count=batch_count,
    )


@router.get("", response_model=list[CourseOut])
def list_courses(
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> list[CourseOut]:
    business = _caller_business(db, user)
    courses = list(
        db.scalars(
            select(Course)
            .where(Course.business_id == business.id)
            .order_by(Course.subject, Course.grade)
        ).all()
    )
    counts = _batch_counts(db, [c.id for c in courses])
    return [_to_out(c, counts.get(c.id, 0)) for c in courses]


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(
    body: CourseIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> CourseOut:
    business = _caller_business(db, user)
    try:
        course = Course(
            business_id=business.id,
            subject=body.subject,
            grade=body.grade,
            is_active=body.is_active,
        )
        db.add(course)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=COURSE_CONFLICT_DETAIL)
    return _to_out(course, 0)


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: uuid.UUID,
    body: CourseUpdate,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> CourseOut:
    business = _caller_business(db, user)
    course = _load_course(db, business, course_id)
    changes = body.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(course, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=COURSE_CONFLICT_DETAIL)

    counts = _batch_counts(db, [course.id])
    return _to_out(course, counts.get(course.id, 0))


@router.delete("/{course_id}", response_model=CourseOut)
def deactivate_course(
    course_id: uuid.UUID,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> CourseOut:
    # Courses are never hard-deleted: DELETE only sets is_active = false.
    business = _caller_business(db, user)
    course = _load_course(db, business, course_id)
    course.is_active = False
    db.commit()

    counts = _batch_counts(db, [course.id])
    return _to_out(course, counts.get(course.id, 0))
