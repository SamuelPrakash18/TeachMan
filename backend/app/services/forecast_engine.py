"""Pure cash-flow forecast engine.

No database access and no clock reads: every date is passed in by the caller.
All money is integer paise; no floats are used in calculations.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

ASSUMPTIONS: list[str] = [
    "Collections use invoice due dates as estimated collection dates",
    "Overdue invoices are expected on the start date",
    "Only unpaid expenses are counted as outflows",
    "Verified payments are actual cash and are not forecast again",
    "All figures are estimates, not guaranteed collections",
]


def _to_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _fmt_rupees(paise: int) -> str:
    return f"₹{paise / 100:,.2f}"


def build_forecast(
    opening_cash_paise: int,
    start_date: date,
    days: int,
    invoices: list[dict],
    expenses: list[dict],
    overrides: dict | None = None,
) -> dict:
    if days < 1:
        raise ValueError("days must be at least 1")

    overrides = overrides or {}
    end_date = start_date + timedelta(days=days - 1)

    collections = [0] * days
    outflows = [0] * days
    outside_collections = 0
    outside_expenses = 0
    inflow_items: list[dict] = []
    outflow_items: list[dict] = []

    for inv in invoices:
        amount = int(inv["outstanding_paise"])
        raw_due = overrides.get(str(inv["id"]), inv["due_date"])
        expected = max(_to_date(raw_due), start_date)
        if expected > end_date:
            outside_collections += amount
            continue
        collections[(expected - start_date).days] += amount
        inflow_items.append(
            {
                "id": inv["id"],
                "student_name": inv["student_name"],
                "amount_paise": amount,
                "expected_date": expected,
            }
        )

    for exp in expenses:
        amount = int(exp["amount_paise"])
        due = max(_to_date(exp["due_date"]), start_date)
        if due > end_date:
            outside_expenses += amount
            continue
        outflows[(due - start_date).days] += amount
        outflow_items.append(
            {
                "id": exp["id"],
                "title": exp["title"],
                "amount_paise": amount,
                "due_date": due,
            }
        )

    daily: list[dict] = []
    closing = int(opening_cash_paise)
    shortage_date: date | None = None

    for i in range(days):
        closing = closing + collections[i] - outflows[i]
        row_date = start_date + timedelta(days=i)
        daily.append(
            {
                "date": row_date,
                "expected_collections_paise": collections[i],
                "expected_expenses_paise": outflows[i],
                "closing_paise": closing,
            }
        )
        if closing < 0 and shortage_date is None:
            shortage_date = row_date

    # Lowest is taken over the daily closings, not the opening balance.
    lowest = min(row["closing_paise"] for row in daily)
    lowest_date = next(row["date"] for row in daily if row["closing_paise"] == lowest)

    return {
        "start_date": start_date,
        "days": days,
        "actual_cash_paise": int(opening_cash_paise),
        "expected_collections_paise": sum(collections),
        "expected_expenses_paise": sum(outflows),
        "projected_closing_paise": daily[-1]["closing_paise"],
        "lowest_closing_paise": lowest,
        "lowest_closing_date": lowest_date,
        "shortage_date": shortage_date,
        "outside_window_paise": outside_collections,
        "outside_window_expenses_paise": outside_expenses,
        "assumptions": list(ASSUMPTIONS),
        "daily": daily,
        "inflow_items": inflow_items,
        "outflow_items": outflow_items,
    }


def compare_forecasts(original: dict, simulated: dict) -> dict:
    new_shortage_dates: list[date] = []
    for orig_row, sim_row in zip(original["daily"], simulated["daily"]):
        if sim_row["closing_paise"] < 0 and orig_row["closing_paise"] >= 0:
            new_shortage_dates.append(sim_row["date"])

    return {
        "original_closing_paise": original["projected_closing_paise"],
        "simulated_closing_paise": simulated["projected_closing_paise"],
        "difference_paise": simulated["projected_closing_paise"]
        - original["projected_closing_paise"],
        "original_lowest_paise": original["lowest_closing_paise"],
        "simulated_lowest_paise": simulated["lowest_closing_paise"],
        "original_lowest_date": original["lowest_closing_date"],
        "simulated_lowest_date": simulated["lowest_closing_date"],
        "original_shortage_date": original["shortage_date"],
        "simulated_shortage_date": simulated["shortage_date"],
        "new_shortage_dates": new_shortage_dates,
    }


def recommendations(comparison: dict) -> list[str]:
    tips: list[str] = []

    sim_shortage = comparison["simulated_shortage_date"]
    orig_shortage = comparison["original_shortage_date"]
    if sim_shortage and not orig_shortage:
        tips.append(
            "Chase the delayed invoice or arrange a buffer before "
            f"{sim_shortage.isoformat()} to avoid a cash shortfall"
        )
    elif sim_shortage and orig_shortage:
        tips.append(
            "A cash shortage is projected even without the change; "
            f"arrange a buffer before {orig_shortage.isoformat()}"
        )

    diff = comparison["difference_paise"]
    if diff < 0:
        tips.append(
            f"The delay lowers projected closing cash by {_fmt_rupees(abs(diff))}"
        )

    if sim_shortage is None:
        tips.append("No cash shortage is projected in this window")

    return tips
