from itertools import product

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.db.session import get_db
from app.models.business import Business, BusinessAddress
from app.models.teaching import Course
from app.models.user import Tutor, User
from app.schemas.tutor import TutorProfileOut, TutorProfileUpdate

router = APIRouter(prefix="/api/tutor", tags=["tutor"])

_TUTOR_FIELDS = {"display_name"}
_ADDRESS_FIELDS = {"door_no", "street", "district", "pin_code", "state"}
_BUSINESS_FIELDS = {"tuition_name", "subjects", "grades", "teaching_timings", "teaching_mode", "upi_id"}


def _load_profile(db: Session, user: User) -> tuple[Tutor, Business, BusinessAddress]:
    tutor = db.scalar(select(Tutor).where(Tutor.user_id == user.id))
    if tutor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor profile not found")
    business = db.scalar(select(Business).where(Business.tutor_id == tutor.id))
    if business is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    address = db.scalar(select(BusinessAddress).where(BusinessAddress.business_id == business.id))
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business address not found")
    return tutor, business, address


def _to_out(user: User, tutor: Tutor, business: Business, address: BusinessAddress) -> TutorProfileOut:
    return TutorProfileOut(
        display_name=tutor.display_name,
        phone=user.phone,
        public_id=tutor.public_id,
        tuition_name=business.tuition_name,
        door_no=address.door_no,
        street=address.street,
        district=address.district,
        pin_code=address.pin_code,
        state=address.state,
        subjects=list(business.subjects),
        grades=list(business.grades),
        teaching_timings=business.teaching_timings,
        teaching_mode=business.teaching_mode,
        upi_id=business.upi_id,
    )


@router.get("/profile", response_model=TutorProfileOut)
def get_profile(
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> TutorProfileOut:
    tutor, business, address = _load_profile(db, user)
    return _to_out(user, tutor, business, address)


@router.put("/profile", response_model=TutorProfileOut)
def update_profile(
    body: TutorProfileUpdate,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> TutorProfileOut:
    tutor, business, address = _load_profile(db, user)
    changes = body.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if field in _TUTOR_FIELDS:
            setattr(tutor, field, value)
        elif field in _ADDRESS_FIELDS:
            setattr(address, field, value)
        elif field in _BUSINESS_FIELDS:
            setattr(business, field, value)

    if "subjects" in changes or "grades" in changes:
        existing = set(
            db.execute(
                select(Course.subject, Course.grade).where(Course.business_id == business.id)
            ).all()
        )
        for subject, grade in dict.fromkeys(product(business.subjects, business.grades)):
            if (subject, grade) not in existing:
                db.add(Course(business_id=business.id, subject=subject, grade=grade))

    db.commit()
    return _to_out(user, tutor, business, address)
