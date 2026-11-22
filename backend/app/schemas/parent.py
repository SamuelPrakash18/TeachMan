import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ChildIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    grade: str = Field(min_length=1, max_length=20)
    address: str | None = Field(default=None, max_length=500)


class ChildUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    grade: str | None = Field(default=None, min_length=1, max_length=20)
    address: str | None = Field(default=None, max_length=500)


class ChildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    public_id: str
    name: str
    grade: str
    address: str
    enrolled_on: date


class ParentDashboardOut(BaseModel):
    parent_name: str
    children_count: int
    outstanding_paise: int
    overdue_count: int
    pending_claims_count: int
    pending_enrollments_count: int
    next_due_date: date | None = None
