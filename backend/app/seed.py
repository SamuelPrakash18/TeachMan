"""Idempotent demo data seed.

Run from the backend/ directory:

    python -m app.seed

If the demo tutor (phone 9800000001) already exists, the script prints
'already seeded' and exits without changing anything.
"""

import datetime as dt
import uuid

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    Batch,
    BatchSchedule,
    Business,
    BusinessAddress,
    CashSnapshot,
    Course,
    Enrollment,
    Expense,
    Invoice,
    InvoiceItem,
    Notification,
    Parent,
    ParentStudentLink,
    Payment,
    PaymentClaim,
    Student,
    Tutor,
    User,
)

DEMO_PASSWORD = "Demo@1234"
TUTOR_PHONE = "9800000001"
PARENT_PHONE = "9800000002"
PARENT2_PHONE = "9800000003"


def days_ago(n: int) -> dt.date:
    return dt.date.today() - dt.timedelta(days=n)


def days_ahead(n: int) -> dt.date:
    return dt.date.today() + dt.timedelta(days=n)


def seed(db) -> bool:
    """Insert all demo data. Returns False if already seeded (nothing added)."""
    existing = db.scalar(select(User).where(User.phone == TUTOR_PHONE))
    if existing is not None:
        print("already seeded")
        return False

    now = dt.datetime.now(dt.timezone.utc)
    today = dt.date.today()
    password_hash = hash_password(DEMO_PASSWORD)

    # ---- Tutor, business, address, courses --------------------------------
    tutor_user_id = uuid.uuid4()
    tutor_user = User(
        id=tutor_user_id,
        phone=TUTOR_PHONE,
        password_hash=password_hash,
        role="tutor",
        status="active",
    )
    db.add(tutor_user)

    tutor_id = uuid.uuid4()
    db.add(
        Tutor(
            id=tutor_id,
            user_id=tutor_user_id,
            public_id="TUT-000001",
            display_name="Ravi Kumar",
        )
    )

    business_id = uuid.uuid4()
    subjects = ["Mathematics", "Science"]
    grades = ["Grade 8", "Grade 9", "Grade 10"]
    db.add(
        Business(
            id=business_id,
            tutor_id=tutor_id,
            tuition_name="Ravi Maths & Science Academy",
            subjects=subjects,
            grades=grades,
            teaching_timings="Mon-Sat 4pm-8pm",
            teaching_mode="hybrid",
            upi_id="ravi.academy@upi",
        )
    )
    db.add(
        BusinessAddress(
            id=uuid.uuid4(),
            business_id=business_id,
            door_no="12A",
            street="MG Road",
            district="Chennai",
            pin_code="600001",
            state="Tamil Nadu",
        )
    )

    courses: dict[tuple[str, str], uuid.UUID] = {}
    for subject in subjects:
        for grade in grades:
            course_id = uuid.uuid4()
            courses[(subject, grade)] = course_id
            db.add(
                Course(
                    id=course_id,
                    business_id=business_id,
                    subject=subject,
                    grade=grade,
                    is_active=True,
                )
            )

    # ---- Parents -----------------------------------------------------------
    parent1_user_id = uuid.uuid4()
    db.add(
        User(
            id=parent1_user_id,
            phone=PARENT_PHONE,
            password_hash=password_hash,
            role="parent",
            status="active",
        )
    )
    parent1_id = uuid.uuid4()
    db.add(
        Parent(
            id=parent1_id,
            user_id=parent1_user_id,
            display_name="Lakshmi Iyer",
            public_id=None,
        )
    )

    parent2_user_id = uuid.uuid4()
    db.add(
        User(
            id=parent2_user_id,
            phone=PARENT2_PHONE,
            password_hash=password_hash,
            role="parent",
            status="active",
        )
    )
    parent2_id = uuid.uuid4()
    db.add(
        Parent(
            id=parent2_id,
            user_id=parent2_user_id,
            display_name="Suresh Menon",
            public_id=None,
        )
    )

    # ---- Students ----------------------------------------------------------
    arjun_id = uuid.uuid4()
    meera_id = uuid.uuid4()
    kavin_id = uuid.uuid4()
    divya_id = uuid.uuid4()
    db.add_all(
        [
            Student(
                id=arjun_id,
                public_id="STU-000001",
                business_id=business_id,
                name="Arjun Iyer",
                grade="Grade 9",
                address="45 Anna Nagar, Chennai",
                enrolled_on=days_ago(90),
            ),
            Student(
                id=meera_id,
                public_id="STU-000002",
                business_id=business_id,
                name="Meera Menon",
                grade="Grade 10",
                address="12 Adyar, Chennai",
                enrolled_on=days_ago(60),
            ),
            Student(
                id=kavin_id,
                public_id="STU-000003",
                business_id=business_id,
                name="Kavin Raj",
                grade="Grade 8",
                address="7 T Nagar, Chennai",
                enrolled_on=days_ago(30),
            ),
            Student(
                id=divya_id,
                public_id="STU-000004",
                business_id=business_id,
                name="Divya Shankar",
                grade="Grade 10",
                address="3 Velachery, Chennai",
                enrolled_on=days_ago(45),
            ),
        ]
    )

    db.add(
        ParentStudentLink(id=uuid.uuid4(), parent_id=parent1_id, student_id=arjun_id)
    )
    db.add(
        ParentStudentLink(id=uuid.uuid4(), parent_id=parent2_id, student_id=meera_id)
    )

    # ---- Batches and schedules ---------------------------------------------
    maths_batch_id = uuid.uuid4()
    db.add(
        Batch(
            id=maths_batch_id,
            business_id=business_id,
            course_id=courses[("Mathematics", "Grade 9")],
            name="Class 9 Maths Morning",
            monthly_fee_paise=500000,
            capacity=20,
            teaching_mode="offline",
            status="active",
        )
    )
    for weekday in (0, 2):
        db.add(
            BatchSchedule(
                id=uuid.uuid4(),
                batch_id=maths_batch_id,
                weekday=weekday,
                start_time=dt.time(7, 0),
                end_time=dt.time(8, 0),
                location="Centre room 1",
                meeting_link=None,
            )
        )

    science_batch_id = uuid.uuid4()
    db.add(
        Batch(
            id=science_batch_id,
            business_id=business_id,
            course_id=courses[("Science", "Grade 10")],
            name="Class 10 Science Evening",
            monthly_fee_paise=600000,
            capacity=15,
            teaching_mode="hybrid",
            status="active",
        )
    )
    for weekday in (1, 3):
        db.add(
            BatchSchedule(
                id=uuid.uuid4(),
                batch_id=science_batch_id,
                weekday=weekday,
                start_time=dt.time(18, 0),
                end_time=dt.time(19, 30),
                location="Centre room 2",
                meeting_link="https://meet.example.com/class10-science",
            )
        )

    # ---- Enrollments -------------------------------------------------------
    # Kavin's 'requested' enrolment is not created: enrollments.parent_id is
    # NOT NULL and Kavin has no parent link in the demo data.
    db.add(
        Enrollment(
            id=uuid.uuid4(),
            business_id=business_id,
            student_id=arjun_id,
            batch_id=maths_batch_id,
            parent_id=parent1_id,
            status="approved",
            decided_at=now,
        )
    )
    db.add(
        Enrollment(
            id=uuid.uuid4(),
            business_id=business_id,
            student_id=meera_id,
            batch_id=science_batch_id,
            parent_id=parent2_id,
            status="approved",
            decided_at=now,
        )
    )

    # ---- Invoices and items ------------------------------------------------
    inv1_id = uuid.uuid4()
    inv2_id = uuid.uuid4()
    inv3_id = uuid.uuid4()
    inv4_id = uuid.uuid4()
    invoices = [
        Invoice(
            id=inv1_id,
            business_id=business_id,
            student_id=arjun_id,
            parent_id=parent1_id,
            invoice_number="INV-000001",
            invoice_date=days_ago(40),
            due_date=days_ago(33),
            total_paise=500000,
            paid_paise=500000,
            status="paid",
        ),
        Invoice(
            id=inv2_id,
            business_id=business_id,
            student_id=arjun_id,
            parent_id=parent1_id,
            invoice_number="INV-000002",
            invoice_date=days_ago(10),
            due_date=days_ago(3),
            total_paise=500000,
            paid_paise=200000,
            status="partially_paid",
        ),
        Invoice(
            id=inv3_id,
            business_id=business_id,
            student_id=meera_id,
            parent_id=parent2_id,
            invoice_number="INV-000003",
            invoice_date=days_ago(20),
            due_date=days_ago(13),
            total_paise=600000,
            paid_paise=0,
            status="overdue",
        ),
        Invoice(
            id=inv4_id,
            business_id=business_id,
            student_id=meera_id,
            parent_id=parent2_id,
            invoice_number="INV-000004",
            invoice_date=today,
            due_date=days_ahead(7),
            total_paise=600000,
            paid_paise=0,
            status="issued",
        ),
    ]
    item_specs = {
        inv1_id: ("Monthly fee - Class 9 Maths Morning", 500000),
        inv2_id: ("Monthly fee - Class 9 Maths Morning", 500000),
        inv3_id: ("Monthly fee - Class 10 Science Evening", 600000),
        inv4_id: ("Monthly fee - Class 10 Science Evening", 600000),
    }
    db.add_all(invoices)
    for inv_id, (description, amount) in item_specs.items():
        db.add(
            InvoiceItem(
                id=uuid.uuid4(),
                invoice_id=inv_id,
                description=description,
                quantity=1,
                unit_paise=amount,
                amount_paise=amount,
            )
        )

    # ---- Payments and payment claims ---------------------------------------
    db.add(
        Payment(
            id=uuid.uuid4(),
            business_id=business_id,
            invoice_id=inv1_id,
            amount_paise=500000,
            method="upi",
            reference="UPI-REF-0001",
            paid_on=days_ago(35),
            recorded_by_user_id=tutor_user_id,
        )
    )
    db.add(
        Payment(
            id=uuid.uuid4(),
            business_id=business_id,
            invoice_id=inv2_id,
            amount_paise=200000,
            method="cash",
            reference=None,
            paid_on=days_ago(8),
            recorded_by_user_id=tutor_user_id,
        )
    )
    db.add(
        PaymentClaim(
            id=uuid.uuid4(),
            business_id=business_id,
            invoice_id=inv4_id,
            parent_id=parent2_id,
            amount_paise=300000,
            upi_reference="UPI-REF-0042",
            status="pending",
            submitted_at=now,
        )
    )

    # ---- Expenses ----------------------------------------------------------
    db.add_all(
        [
            Expense(
                id=uuid.uuid4(),
                business_id=business_id,
                title="Tuition centre rent",
                category="rent",
                amount_paise=1200000,
                due_date=days_ahead(5),
                is_recurring=True,
                status="unpaid",
            ),
            Expense(
                id=uuid.uuid4(),
                business_id=business_id,
                title="Internet",
                category="internet",
                amount_paise=89900,
                due_date=days_ahead(12),
                status="unpaid",
            ),
            Expense(
                id=uuid.uuid4(),
                business_id=business_id,
                title="Teaching materials",
                category="materials",
                amount_paise=250000,
                due_date=days_ahead(20),
                status="unpaid",
            ),
            Expense(
                id=uuid.uuid4(),
                business_id=business_id,
                title="Electricity",
                category="electricity",
                amount_paise=180000,
                due_date=days_ahead(30),
                status="unpaid",
            ),
            Expense(
                id=uuid.uuid4(),
                business_id=business_id,
                title="Electricity (last month)",
                category="electricity",
                amount_paise=170000,
                due_date=days_ago(25),
                paid_on=days_ago(24),
                status="paid",
            ),
        ]
    )

    # ---- Cash snapshot -----------------------------------------------------
    db.add(
        CashSnapshot(
            id=uuid.uuid4(),
            business_id=business_id,
            opening_cash_paise=1500000,
            as_of_date=today,
        )
    )

    # ---- Notifications -----------------------------------------------------
    db.add_all(
        [
            Notification(
                id=uuid.uuid4(),
                user_id=tutor_user_id,
                title="New payment claim received",
                body="Suresh Menon submitted a UPI payment claim of Rs 3,000 for INV-000004.",
                link=None,
            ),
            Notification(
                id=uuid.uuid4(),
                user_id=parent1_user_id,
                title="Enrollment approved",
                body="Arjun Iyer's enrolment in Class 9 Maths Morning has been approved.",
                link=None,
            ),
        ]
    )

    return True


def main() -> None:
    db = SessionLocal()
    try:
        if not seed(db):
            return
        db.commit()
        print("Demo data seeded successfully.")
        print()
        print("Demo logins (password for all: Demo@1234)")
        print("  Tutor:    phone 9800000001  (Ravi Kumar, TUT-000001)")
        print("  Parent:   phone 9800000002  (Lakshmi Iyer, parent of Arjun Iyer)")
        print("  Parent:   phone 9800000003  (Suresh Menon, parent of Meera Menon)")
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"Seeding failed, all changes rolled back: {exc}")
        raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
