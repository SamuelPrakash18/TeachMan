from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import Invoice, InvoiceItem
from app.models.student import ParentStudentLink, Student
from app.models.teaching import Batch, Enrollment
from app.services.invoice_service import next_invoice_number


def on_enrollment_approved(db: Session, enrollment: Enrollment) -> None:
    """Create the first monthly invoice when an enrollment is approved.

    Does not commit; the calling route owns the transaction.
    """
    batch = db.get(Batch, enrollment.batch_id)
    student = db.get(Student, enrollment.student_id)
    if batch is None or student is None:
        return

    parent_id = db.execute(
        select(ParentStudentLink.parent_id)
        .where(ParentStudentLink.student_id == student.id)
        .limit(1)
    ).scalar_one_or_none()

    today = date.today()
    fee = int(batch.monthly_fee_paise or 0)

    invoice = Invoice(
        business_id=student.business_id,
        student_id=student.id,
        parent_id=parent_id,
        invoice_number=next_invoice_number(db, student.business_id),
        invoice_date=today,
        due_date=today + timedelta(days=7),
        total_paise=fee,
        paid_paise=0,
        status="issued",
    )
    db.add(invoice)
    db.flush()

    db.add(
        InvoiceItem(
            invoice_id=invoice.id,
            description=batch.name,
            quantity=1,
            unit_paise=fee,
            amount_paise=fee,
        )
    )
