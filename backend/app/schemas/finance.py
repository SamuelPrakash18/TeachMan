"""Pydantic schemas for invoices, payments, payment claims and expenses."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------- Invoices ----------

class InvoiceItemIn(BaseModel):
    description: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_paise: int = Field(ge=0)


class InvoiceIn(BaseModel):
    student_id: UUID
    parent_id: Optional[UUID] = None
    invoice_date: date
    due_date: date
    items: list[InvoiceItemIn] = Field(min_length=1)

    @model_validator(mode="after")
    def _due_after_invoice(self):
        if self.due_date < self.invoice_date:
            raise ValueError("due_date must be on or after invoice_date")
        return self


class InvoiceUpdate(BaseModel):
    due_date: Optional[date] = None


class InvoiceItemOut(BaseModel):
    description: str
    quantity: int
    unit_paise: int
    amount_paise: int


class InvoiceOut(BaseModel):
    id: UUID
    invoice_number: str
    student_id: UUID
    student_name: str
    parent_name: Optional[str] = None
    invoice_date: date
    due_date: date
    total_paise: int
    paid_paise: int
    outstanding_paise: int
    status: str
    days_overdue: int
    items: list[InvoiceItemOut]


# ---------- Payments ----------

class PaymentIn(BaseModel):
    invoice_id: UUID
    amount_paise: int = Field(gt=0)
    method: Literal["cash", "upi", "bank", "other"]
    reference: Optional[str] = None
    paid_on: date


class PaymentOut(BaseModel):
    id: UUID
    invoice_id: UUID
    invoice_number: str
    amount_paise: int
    method: str
    reference: Optional[str] = None
    paid_on: date


# ---------- Payment claims (parent-submitted UPI payments) ----------

class PaymentClaimIn(BaseModel):
    invoice_id: UUID
    amount_paise: int = Field(gt=0)
    upi_reference: str = Field(min_length=4, max_length=64)


class PaymentClaimOut(BaseModel):
    id: UUID
    invoice_id: UUID
    invoice_number: str
    parent_name: Optional[str] = None
    amount_paise: int
    upi_reference: str
    status: str
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None


# ---------- Expenses ----------

ExpenseCategory = Literal[
    "rent", "electricity", "internet", "salary", "materials", "transport", "other"
]


class ExpenseIn(BaseModel):
    title: str = Field(min_length=1)
    category: ExpenseCategory
    amount_paise: int = Field(gt=0)
    due_date: date
    is_recurring: bool = False
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    category: Optional[ExpenseCategory] = None
    amount_paise: Optional[int] = Field(default=None, gt=0)
    due_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    notes: Optional[str] = None


class ExpenseOut(BaseModel):
    id: UUID
    title: str
    category: str
    amount_paise: int
    due_date: date
    paid_on: Optional[date] = None
    status: str
    is_recurring: bool
    notes: Optional[str] = None
    overdue: bool


class ExpenseMarkPaidIn(BaseModel):
    paid_on: Optional[date] = None
