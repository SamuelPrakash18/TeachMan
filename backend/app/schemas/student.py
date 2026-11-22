from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class StudentIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    grade: str = Field(min_length=1, max_length=20)
    address: str | None = Field(default=None, max_length=2000)


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    grade: str | None = Field(default=None, min_length=1, max_length=20)
    address: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> "StudentUpdate":
        for name in ("name", "grade"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class StudentOut(BaseModel):
    id: UUID
    public_id: str
    name: str
    grade: str
    address: str
    enrolled_on: date
    parent_name: str | None = None
    parent_phone: str | None = None
