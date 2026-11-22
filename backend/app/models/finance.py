import uuid
from datetime import date, datetime

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
    UniqueConstraint,
    Uuid,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("business_id", "invoice_number", name="uq_invoices_business_number"),
        CheckConstraint("total_paise >= 0", name="ck_invoices_total_paise"),
        CheckConstraint("paid_paise >= 0", name="ck_invoices_paid_paise"),
        CheckConstraint("paid_paise <= total_paise", name="ck_invoices_paid_lte_total"),
        CheckConstraint(
            "status IN ('draft','issued','partially_paid','paid','overdue','cancelled')",
            name="ck_invoices_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("parents.id", ondelete="RESTRICT"), nullable=True
    )
    invoice_number: Mapped[str] = mapped_column(String(30), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_paise: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_invoice_items_quantity"),
        CheckConstraint("unit_paise >= 0", name="ck_invoice_items_unit_paise"),
        CheckConstraint("amount_paise >= 0", name="ck_invoice_items_amount_paise"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="ck_payments_amount_paise"),
        CheckConstraint(
            "method IN ('cash','upi','bank','other')", name="ck_payments_method"
        ),
        Index(
            "uq_payments_business_method_reference",
            "business_id",
            "method",
            "reference",
            unique=True,
            postgresql_where=text("reference IS NOT NULL"),
            sqlite_where=text("reference IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PaymentClaim(Base):
    __tablename__ = "payment_claims"
    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="ck_payment_claims_amount_paise"),
        CheckConstraint(
            "status IN ('pending','under_review','verified','rejected')",
            name="ck_payment_claims_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("parents.id", ondelete="RESTRICT"), nullable=False
    )
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    upi_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    screenshot_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(12), nullable=False, default="pending", server_default="pending"
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True
    )


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="ck_expenses_amount_paise"),
        CheckConstraint(
            "category IN ('rent','electricity','internet','salary','materials','transport','other')",
            name="ck_expenses_category",
        ),
        CheckConstraint("status IN ('unpaid','paid')", name="ck_expenses_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("businesses.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="unpaid", server_default="unpaid"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
