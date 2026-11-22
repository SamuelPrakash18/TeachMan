import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_tutor
from app.db.session import get_db
from app.models.business import Business
from app.models.student import ParentStudentLink, Student
from app.models.teaching import Enrollment, LearningMilestone
from app.models.user import Parent, Tutor, User
from app.schemas.learning import MilestoneIn, MilestoneOut, MilestoneUpdate

router = APIRouter(prefix="/api/learning", tags=["learning"])

APPROVED = "approved"
STUDENT_NOT_FOUND_DETAIL = "Student not found"
MILESTONE_NOT_FOUND_DETAIL = "Milestone not found"
NON_NULLABLE_FIELDS = ("subject", "topic", "status")


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


def _load_owned_milestone(db: Session, business: Business, milestone_id: uuid.UUID) -> LearningMilestone:
    milestone = db.scalar(
        select(LearningMilestone).where(
            LearningMilestone.id == milestone_id,
            LearningMilestone.business_id == business.id,
        )
    )
    if milestone is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MILESTONE_NOT_FOUND_DETAIL)
    return milestone


def _to_out(milestone: LearningMilestone) -> MilestoneOut:
    return MilestoneOut(
        id=milestone.id,
        student_id=milestone.student_id,
        subject=milestone.subject,
        topic=milestone.topic,
        status=milestone.status,
        score=milestone.score,
        notes=milestone.notes,
        updated_at=milestone.updated_at,
    )


@router.post("/milestones", response_model=MilestoneOut, status_code=status.HTTP_201_CREATED)
def create_milestone(
    body: MilestoneIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> MilestoneOut:
    business = _caller_business(db, user)
    if not _tutor_can_see_student(db, business, body.student_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND_DETAIL)

    milestone = LearningMilestone(
        business_id=business.id,
        student_id=body.student_id,
        subject=body.subject,
        topic=body.topic,
        status=body.status,
        score=body.score,
        notes=body.notes,
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return _to_out(milestone)


@router.get("/milestones", response_model=list[MilestoneOut])
def list_milestones(
    student_id: uuid.UUID = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MilestoneOut]:
    stmt = select(LearningMilestone).where(LearningMilestone.student_id == student_id)

    if user.role == "tutor":
        business = _caller_business(db, user)
        if not _tutor_can_see_student(db, business, student_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=STUDENT_NOT_FOUND_DETAIL)
        stmt = stmt.where(LearningMilestone.business_id == business.id)
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

    milestones = db.scalars(stmt.order_by(LearningMilestone.subject, LearningMilestone.topic)).all()
    return [_to_out(m) for m in milestones]


@router.put("/milestones/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: uuid.UUID,
    body: MilestoneUpdate,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> MilestoneOut:
    business = _caller_business(db, user)
    milestone = _load_owned_milestone(db, business, milestone_id)

    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field in NON_NULLABLE_FIELDS:
            continue
        setattr(milestone, field, value)

    db.commit()
    db.refresh(milestone)
    return _to_out(milestone)
