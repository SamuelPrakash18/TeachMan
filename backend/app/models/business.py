import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = (
        CheckConstraint(
            "teaching_mode IN ('offline','online','hybrid')",
            name="ck_businesses_teaching_mode",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tutor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tutors.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    tuition_name: Mapped[str] = mapped_column(String(150), nullable=False)
    subjects: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    grades: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    teaching_timings: Mapped[str] = mapped_column(Text, nullable=False)
    teaching_mode: Mapped[str] = mapped_column(String(10), nullable=False)
    upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    upi_qr_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class BusinessAddress(Base):
    __tablename__ = "business_addresses"
    __table_args__ = (
        CheckConstraint("length(pin_code) = 6", name="ck_business_addresses_pin_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("businesses.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    door_no: Mapped[str] = mapped_column(String(20), nullable=False)
    street: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    pin_code: Mapped[str] = mapped_column(String(6), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
