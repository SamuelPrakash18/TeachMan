"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Identity / users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("role IN ('tutor','parent')", name="ck_users_role"),
        sa.CheckConstraint(
            "status IN ('active','deactivated','deleted')", name="ck_users_status"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )

    op.create_table(
        "tutors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("public_id", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("public_id"),
    )

    op.create_table(
        "parents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("public_id", sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("public_id"),
    )

    # ------------------------------------------------------------------
    # Business
    # ------------------------------------------------------------------
    op.create_table(
        "businesses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "tutor_id",
            sa.Uuid(),
            sa.ForeignKey("tutors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("tuition_name", sa.String(length=150), nullable=False),
        sa.Column("subjects", sa.JSON(), nullable=False),
        sa.Column("grades", sa.JSON(), nullable=False),
        sa.Column("teaching_timings", sa.Text(), nullable=False),
        sa.Column("teaching_mode", sa.String(length=10), nullable=False),
        sa.Column("upi_id", sa.String(length=100), nullable=True),
        sa.Column("upi_qr_key", sa.String(length=255), nullable=True),
        sa.Column("payment_instructions", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "teaching_mode IN ('offline','online','hybrid')",
            name="ck_businesses_teaching_mode",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tutor_id"),
    )

    op.create_table(
        "business_addresses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("door_no", sa.String(length=20), nullable=False),
        sa.Column("street", sa.String(length=200), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("pin_code", sa.String(length=6), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.CheckConstraint(
            "length(pin_code) = 6", name="ck_business_addresses_pin_code"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id"),
    )

    # ------------------------------------------------------------------
    # Students
    # ------------------------------------------------------------------
    op.create_table(
        "students",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(length=20), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("enrolled_on", sa.Date(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )

    op.create_table(
        "parent_student_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "parent_id",
            sa.Uuid(),
            sa.ForeignKey("parents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "parent_id", "student_id", name="uq_parent_student_links_pair"
        ),
    )

    # ------------------------------------------------------------------
    # Teaching
    # ------------------------------------------------------------------
    op.create_table(
        "courses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=80), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_id", "subject", "grade", name="uq_courses_business_subject_grade"
        ),
    )

    op.create_table(
        "batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            sa.Uuid(),
            sa.ForeignKey("courses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("monthly_fee_paise", sa.BigInteger(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("teaching_mode", sa.String(length=10), nullable=False),
        sa.Column(
            "status",
            sa.String(length=10),
            server_default="active",
            nullable=False,
        ),
        sa.CheckConstraint(
            "monthly_fee_paise >= 0", name="ck_batches_monthly_fee_paise"
        ),
        sa.CheckConstraint("capacity > 0", name="ck_batches_capacity"),
        sa.CheckConstraint(
            "teaching_mode IN ('offline','online','hybrid')",
            name="ck_batches_teaching_mode",
        ),
        sa.CheckConstraint(
            "status IN ('active','paused','closed')", name="ck_batches_status"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "batch_schedules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "batch_id",
            sa.Uuid(),
            sa.ForeignKey("batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("meeting_link", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "weekday >= 0 AND weekday <= 6", name="ck_batch_schedules_weekday"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "batch_id",
            sa.Uuid(),
            sa.ForeignKey("batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            sa.Uuid(),
            sa.ForeignKey("parents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('requested','approved','rejected','ended')",
            name="ck_enrollments_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_enrollments_active_student_batch",
        "enrollments",
        ["student_id", "batch_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('requested','approved')"),
        sqlite_where=sa.text("status IN ('requested','approved')"),
    )

    op.create_table(
        "class_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "batch_id",
            sa.Uuid(),
            sa.ForeignKey("batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=12),
            server_default="scheduled",
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('scheduled','conducted','cancelled')",
            name="ck_class_sessions_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "attendance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("class_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.CheckConstraint(
            "status IN ('present','absent','excused')", name="ck_attendance_status"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id", "student_id", name="uq_attendance_session_student"
        ),
    )

    op.create_table(
        "learning_milestones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=80), nullable=False),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.String(length=12),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "status IN ('pending','in_progress','completed')",
            name="ck_learning_milestones_status",
        ),
        sa.CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 100)",
            name="ck_learning_milestones_score",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # Finance
    # ------------------------------------------------------------------
    op.create_table(
        "invoices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            sa.Uuid(),
            sa.ForeignKey("parents.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("invoice_number", sa.String(length=30), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("total_paise", sa.BigInteger(), nullable=False),
        sa.Column(
            "paid_paise",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("total_paise >= 0", name="ck_invoices_total_paise"),
        sa.CheckConstraint("paid_paise >= 0", name="ck_invoices_paid_paise"),
        sa.CheckConstraint("paid_paise <= total_paise", name="ck_invoices_paid_lte_total"),
        sa.CheckConstraint(
            "status IN ('draft','issued','partially_paid','paid','overdue','cancelled')",
            name="ck_invoices_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "business_id", "invoice_number", name="uq_invoices_business_number"
        ),
    )

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "invoice_id",
            sa.Uuid(),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_paise", sa.BigInteger(), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_invoice_items_quantity"),
        sa.CheckConstraint("unit_paise >= 0", name="ck_invoice_items_unit_paise"),
        sa.CheckConstraint("amount_paise >= 0", name="ck_invoice_items_amount_paise"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            sa.Uuid(),
            sa.ForeignKey("invoices.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("reference", sa.String(length=100), nullable=True),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column(
            "recorded_by_user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("amount_paise > 0", name="ck_payments_amount_paise"),
        sa.CheckConstraint(
            "method IN ('cash','upi','bank','other')", name="ck_payments_method"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_payments_business_method_reference",
        "payments",
        ["business_id", "method", "reference"],
        unique=True,
        postgresql_where=sa.text("reference IS NOT NULL"),
        sqlite_where=sa.text("reference IS NOT NULL"),
    )

    op.create_table(
        "payment_claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "invoice_id",
            sa.Uuid(),
            sa.ForeignKey("invoices.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "parent_id",
            sa.Uuid(),
            sa.ForeignKey("parents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("upi_reference", sa.String(length=100), nullable=False),
        sa.Column("screenshot_key", sa.String(length=255), nullable=True),
        sa.Column(
            "status",
            sa.String(length=12),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "payment_id",
            sa.Uuid(),
            sa.ForeignKey("payments.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "amount_paise > 0", name="ck_payment_claims_amount_paise"
        ),
        sa.CheckConstraint(
            "status IN ('pending','under_review','verified','rejected')",
            name="ck_payment_claims_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=True),
        sa.Column(
            "is_recurring",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=10),
            server_default="unpaid",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint("amount_paise > 0", name="ck_expenses_amount_paise"),
        sa.CheckConstraint(
            "category IN ('rent','electricity','internet','salary','materials','transport','other')",
            name="ck_expenses_category",
        ),
        sa.CheckConstraint("status IN ('unpaid','paid')", name="ck_expenses_status"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "cash_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "business_id",
            sa.Uuid(),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "opening_cash_paise",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.CheckConstraint(
            "opening_cash_paise >= 0",
            name="ck_cash_snapshots_opening_cash_paise",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


    # ------------------------------------------------------------------
    # System
    # ------------------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("link", sa.String(length=500), nullable=True),
        sa.Column(
            "is_read",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "account_deletion_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('requested','confirmed','cancelled')",
            name="ck_account_deletion_requests_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "account_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(length=20), nullable=False),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "from_status IN ('active','deactivated','deleted')",
            name="ck_account_status_history_from_status",
        ),
        sa.CheckConstraint(
            "to_status IN ('active','deactivated','deleted')",
            name="ck_account_status_history_to_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    # Reverse dependency order: drop dependents before the tables they reference.
    op.drop_table("account_status_history")
    op.drop_table("account_deletion_requests")
    op.drop_table("activity_logs")
    op.drop_table("notifications")

    op.drop_table("expenses")
    op.drop_table("payment_claims")

    op.drop_index("uq_payments_business_method_reference", table_name="payments")
    op.drop_table("payments")
    op.drop_table("invoice_items")
    op.drop_table("invoices")

    op.drop_table("learning_milestones")
    op.drop_table("attendance")
    op.drop_table("class_sessions")

    op.drop_index("uq_enrollments_active_student_batch", table_name="enrollments")
    op.drop_table("enrollments")
    op.drop_table("batch_schedules")
    op.drop_table("batches")
    op.drop_table("courses")

    op.drop_table("parent_student_links")
    op.drop_table("students")
    op.drop_table("business_addresses")
    op.drop_table("cash_snapshots")
    op.drop_table("businesses")
    op.drop_table("parents")
    op.drop_table("tutors")
    op.drop_table("users")
