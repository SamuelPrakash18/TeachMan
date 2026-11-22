from datetime import date
from itertools import product

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.business import Business, BusinessAddress
from app.models.student import ParentStudentLink, Student
from app.models.system import ActivityLog
from app.models.teaching import Course
from app.models.user import Parent, Tutor, User
from app.schemas.auth import (
    ChangePasswordIn,
    LoginIn,
    ParentRegisterIn,
    TokenOut,
    TutorRegisterIn,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

PHONE_TAKEN_DETAIL = "Phone number already registered"
REGISTRATION_CONFLICT_DETAIL = "Registration conflicts with an existing account"
BAD_CREDENTIALS_DETAIL = "Invalid phone or password"


def _phone_taken(db: Session, phone: str) -> bool:
    return db.scalar(select(User.id).where(User.phone == phone)) is not None


def _next_public_id(db: Session, column, prefix: str) -> str:
    current_max = db.scalar(select(func.max(column)))
    next_number = (int(current_max[len(prefix):]) if current_max else 0) + 1
    return f"{prefix}{next_number:06d}"


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


@router.post("/register/tutor", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_tutor(body: TutorRegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    if _phone_taken(db, body.phone):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=PHONE_TAKEN_DETAIL)

    try:
        user = User(
            phone=body.phone,
            password_hash=hash_password(body.password),
            role="tutor",
        )
        db.add(user)
        db.flush()

        tutor = Tutor(
            user_id=user.id,
            public_id=_next_public_id(db, Tutor.public_id, "TUT-"),
            display_name=body.name,
        )
        db.add(tutor)
        db.flush()

        business = Business(
            tutor_id=tutor.id,
            tuition_name=body.tuition_name,
            subjects=list(body.subjects),
            grades=list(body.grades),
            teaching_timings=body.teaching_timings,
            teaching_mode=body.teaching_mode,
            upi_id=body.upi_id,
        )
        db.add(business)
        db.flush()

        db.add(
            BusinessAddress(
                business_id=business.id,
                door_no=body.door_no,
                street=body.street,
                district=body.district,
                pin_code=body.pin_code,
                state=body.state,
            )
        )

        for subject, grade in dict.fromkeys(product(body.subjects, body.grades)):
            db.add(Course(business_id=business.id, subject=subject, grade=grade))

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=REGISTRATION_CONFLICT_DETAIL)

    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        public_id=tutor.public_id,
    )


@router.post("/register/parent", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_parent(body: ParentRegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    if _phone_taken(db, body.phone):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=PHONE_TAKEN_DETAIL)

    try:
        user = User(
            phone=body.phone,
            password_hash=hash_password(body.password),
            role="parent",
        )
        db.add(user)
        db.flush()

        parent = Parent(user_id=user.id, display_name=body.name, public_id=None)
        db.add(parent)
        db.flush()

        student = Student(
            public_id=_next_public_id(db, Student.public_id, "STU-"),
            business_id=None,
            name=body.student_name,
            grade=body.student_grade,
            address=body.student_address,
            enrolled_on=date.today(),
        )
        db.add(student)
        db.flush()

        db.add(ParentStudentLink(parent_id=parent.id, student_id=student.id))

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=REGISTRATION_CONFLICT_DETAIL)

    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        public_id=None,
    )


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.phone == body.phone))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=BAD_CREDENTIALS_DETAIL)
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    public_id, _ = _identity(db, user)
    return TokenOut(
        access_token=create_access_token(user.id, user.role),
        role=user.role,
        public_id=public_id,
    )


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


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserOut:
    public_id, display_name = _identity(db, user)
    return UserOut(
        id=user.id,
        phone=user.phone,
        role=user.role,
        public_id=public_id,
        display_name=display_name,
    )


@router.put("/change-password")
def change_password(
    body: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"status": "ok"}
