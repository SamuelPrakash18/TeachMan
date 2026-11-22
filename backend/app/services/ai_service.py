"""Deterministic drafts for AI-assisted text.

Every amount, date and name is computed here. NVIDIA, when available, only
polishes wording; it never supplies figures. Nothing in this module sends a
message. Each public function returns (text, source) where source is 'ai' or
'template'.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finance import Expense, Invoice
from app.models.student import Student
from app.services.nvidia_client import ask_nvidia

TONES = ("friendly", "formal", "urgent", "whatsapp")
OPEN_INVOICE_STATUSES = ("issued", "partially_paid", "overdue")
FORECAST_DAYS = 30
TOP_N = 5

NO_INVENTION_RULE = (
    "Do not invent or change any figure, date or name; use only the facts provided."
)


def _rupees(paise: int) -> str:
    return f"₹{paise / 100:,.2f}"


def _polish(system_prompt: str, user_prompt: str, template: str) -> tuple[str, str]:
    polished = ask_nvidia(system_prompt, user_prompt)
    if polished:
        return polished, "ai"
    return template, "template"


def draft_reminder(
    tone: str,
    student_name: str,
    parent_name: str | None,
    invoice_number: str,
    outstanding_paise: int,
    due_date_iso: str,
    days_overdue: int,
) -> tuple[str, str]:
    if tone not in TONES:
        raise ValueError(f"Unsupported tone: {tone}")

    greeting_name = parent_name or "Parent"
    amount = _rupees(outstanding_paise)

    if tone == "formal":
        template = (
            f"Dear {greeting_name}, this is a formal reminder that invoice {invoice_number} "
            f"for {student_name} has an outstanding balance of {amount}, due on {due_date_iso}"
            + (f" and now {days_overdue} day(s) overdue" if days_overdue > 0 else "")
            + ". Kindly arrange payment at your earliest convenience. Thank you."
        )
    elif tone == "urgent":
        template = (
            f"Dear {greeting_name}, URGENT: invoice {invoice_number} for {student_name} "
            f"has {amount} outstanding"
            + (f", {days_overdue} day(s) overdue" if days_overdue > 0 else f", due {due_date_iso}")
            + ". Please pay immediately or contact us today to avoid interruption."
        )
    elif tone == "whatsapp":
        template = (
            f"Hi {greeting_name}, a quick note: invoice {invoice_number} for {student_name} "
            f"has {amount} pending (due {due_date_iso})"
            + (f", {days_overdue} day(s) overdue" if days_overdue > 0 else "")
            + ". Please let us know once paid. Thanks!"
        )
    else:
        template = (
            f"Hello {greeting_name}, a friendly reminder that invoice {invoice_number} "
            f"for {student_name} has {amount} outstanding, due on {due_date_iso}"
            + (f" ({days_overdue} day(s) overdue)" if days_overdue > 0 else "")
            + ". Thank you for your support!"
        )

    system_prompt = (
        "You polish short fee-reminder messages for a tutor. "
        "Keep the same meaning and tone. " + NO_INVENTION_RULE + " "
        "Keep every rupee amount, date, invoice number and name exactly as given. "
        "Return only the message text."
    )
    user_prompt = (
        f"Tone: {tone}\n"
        f"Parent name: {greeting_name}\n"
        f"Student name: {student_name}\n"
        f"Invoice number: {invoice_number}\n"
        f"Outstanding amount: {amount}\n"
        f"Due date: {due_date_iso}\n"
        f"Days overdue: {days_overdue}\n\n"
        f"Draft to polish:\n{template}"
    )
    return _polish(system_prompt, user_prompt, template)


def explain_cashflow(facts: dict) -> tuple[str, str]:
    shortage = facts.get("shortage_date")
    projected = int(facts.get("projected_closing_paise", 0))
    lowest = int(facts.get("lowest_closing_paise", 0))
    outflows = facts.get("top_outflows", []) or []
    outflow_titles = ", ".join(str(item.get("title", "")) for item in outflows[:5]) or "none"

    if shortage:
        opening_line = f"A cash shortage is projected starting {shortage}."
    else:
        opening_line = "No cash shortage is projected in this window."

    template = (
        f"{opening_line} Projected closing cash is {_rupees(projected)}, "
        f"and the lowest daily closing is {_rupees(lowest)}. "
        f"Main upcoming outflows: {outflow_titles}."
    )

    system_prompt = (
        "You explain a cash-flow forecast to a tutor in plain language. "
        + NO_INVENTION_RULE
        + " Do not compute new balances. Return only the explanation text."
    )
    user_prompt = f"Facts (JSON-like): {facts}\n\nDraft to polish:\n{template}"
    return _polish(system_prompt, user_prompt, template)


def fallback_summary(facts: dict) -> str:
    outstanding = _rupees(int(facts.get("outstanding_total_paise", 0)))
    overdue_count = int(facts.get("overdue_count", 0))
    expected_in = _rupees(int(facts.get("expected_30d_collections_paise", 0)))
    expected_out = _rupees(int(facts.get("expected_30d_expenses_paise", 0)))
    return (
        "AI is unavailable right now. Here are your key figures: "
        f"outstanding total {outstanding}; overdue invoices {overdue_count}; "
        f"expected collections in 30 days {expected_in}; "
        f"expected expenses in 30 days {expected_out}."
    )


def build_business_facts(db: Session, business_id: Any) -> dict:
    today = date.today()
    window_end = today + timedelta(days=FORECAST_DAYS)

    outstanding_expr = Invoice.total_paise - Invoice.paid_paise
    open_filter = (
        Invoice.business_id == business_id,
        Invoice.status.in_(OPEN_INVOICE_STATUSES),
    )

    outstanding_total = db.scalar(
        select(func.coalesce(func.sum(outstanding_expr), 0)).where(*open_filter)
    ) or 0
    overdue_filter = (*open_filter, Invoice.due_date < today)
    overdue_count = db.scalar(select(func.count(Invoice.id)).where(*overdue_filter)) or 0
    overdue_total = db.scalar(
        select(func.coalesce(func.sum(outstanding_expr), 0)).where(*overdue_filter)
    ) or 0
    expected_collections = db.scalar(
        select(func.coalesce(func.sum(outstanding_expr), 0)).where(
            *open_filter, Invoice.due_date <= window_end
        )
    ) or 0
    expected_expenses = db.scalar(
        select(func.coalesce(func.sum(Expense.amount_paise), 0)).where(
            Expense.business_id == business_id,
            Expense.status == "unpaid",
            Expense.due_date <= window_end,
        )
    ) or 0

    top_overdue_rows = db.execute(
        select(Invoice.invoice_number, Student.name, Invoice.due_date, outstanding_expr)
        .join(Student, Student.id == Invoice.student_id)
        .where(*overdue_filter)
        .order_by(Invoice.due_date)
        .limit(TOP_N)
    ).all()
    top_upcoming_rows = db.execute(
        select(Expense.title, Expense.due_date, Expense.amount_paise)
        .where(
            Expense.business_id == business_id,
            Expense.status == "unpaid",
        )
        .order_by(Expense.due_date)
        .limit(TOP_N)
    ).all()

    return {
        "as_of": today.isoformat(),
        "outstanding_total_paise": int(outstanding_total),
        "overdue_count": int(overdue_count),
        "overdue_total_paise": int(overdue_total),
        "expected_30d_collections_paise": int(expected_collections),
        "expected_30d_expenses_paise": int(expected_expenses),
        "top_overdue_invoices": [
            {
                "invoice_number": number,
                "student_name": name,
                "due_date": due.isoformat(),
                "outstanding_paise": int(amount),
            }
            for number, name, due, amount in top_overdue_rows
        ],
        "top_unpaid_expenses": [
            {
                "title": title,
                "due_date": due.isoformat(),
                "amount_paise": int(amount),
            }
            for title, due, amount in top_upcoming_rows
        ],
    }


def answer_question(question: str, facts: dict) -> tuple[str, str]:
    fallback = fallback_summary(facts)

    system_prompt = (
        "You are a read-only assistant for a tutor's business. "
        "Answer only from the JSON facts provided. "
        + NO_INVENTION_RULE
        + " If the facts do not cover the question, say so. Never send messages or take actions."
    )
    user_prompt = f"Facts (JSON): {facts}\n\nQuestion: {question}"
    polished = ask_nvidia(system_prompt, user_prompt)
    if polished:
        return polished, "ai"
    return fallback, "template"
