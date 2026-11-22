from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class CashSnapshotIn(BaseModel):
    opening_cash_paise: int = Field(ge=0)
    as_of_date: date | None = None


class CashSnapshotOut(BaseModel):
    opening_cash_paise: int
    as_of_date: date | None = None


class SimulateIn(BaseModel):
    invoice_id: UUID
    delay_days: int = Field(ge=0, le=180)
    days: Literal[30, 60, 90] = 30


class ForecastResponse(BaseModel):
    days: int
    actual_cash_paise: int
    expected_collections_paise: int
    expected_expenses_paise: int
    projected_closing_paise: int
    lowest_closing_paise: int
    lowest_closing_date: date
    shortage_date: date | None = None
    assumptions: list[str]
    daily: list[dict[str, Any]]
    inflow_items: list[dict[str, Any]]
    outflow_items: list[dict[str, Any]]
    outside_window_expenses_paise: int = 0
