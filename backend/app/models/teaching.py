import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("business_id", "subject", "grade", name="uq_courses_business_subject_grade"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(80), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )


class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (
        CheckConstraint("monthly_fee_paise >= 0", name="ck_batches_monthly_fee_paise"),
        CheckConstraint("capacity > 0", name="ck_batches_capacity"),
        CheckConstraint(
            "teaching_mode IN ('offline','online','hybrid')",
            name="ck_batches_teaching_mode",
        ),
        CheckConstraint(
            "status IN ('active','paused','closed')", name="ck_batches_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    monthly_fee_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    teaching_mode: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="active", server_default="active"
    )


class BatchSchedule(Base):
    __tablename__ = "batch_schedules"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_batch_schedules_weekday"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    location: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(Text, nullable=True)


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('requested','approved','rejected','ended')",
            name="ck_enrollments_status",
        ),
        Index(
            "uq_enrollments_active_student_batch",
            "student_id",
            "batch_id",
            unique=True,
            postgresql_where=text("status IN ('requested','approved')"),
            sqlite_where=text("status IN ('requested','approved')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("parents.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ClassSession(Base):
    __tablename__ = "class_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled','conducted','cancelled')",
            name="ck_class_sessions_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("batches.id", ondelete="RESTRICT"), nullable=False
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(12), nullable=False, default="scheduled", server_default="scheduled"
    )


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),
        CheckConstraint(
            "status IN ('present','absent','excused')", name="ck_attendance_status"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False)


class LearningMilestone(Base):
    __tablename__ = "learning_milestones"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','in_progress','completed')",
            name="ck_learning_milestones_status",
        ),
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_learning_milestones_score",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(80), nullable=False)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(12), nullable=False, default="pending", server_default="pending"
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
