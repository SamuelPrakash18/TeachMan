from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

TeachingMode = Literal["offline", "online", "hybrid"]
BatchStatus = Literal["active", "paused", "closed"]
EnrollmentStatus = Literal["requested", "approved", "rejected", "ended"]

_TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"


class CourseIn(BaseModel):
    subject: str = Field(min_length=1, max_length=80)
    grade: str = Field(min_length=1, max_length=20)
    is_active: bool = True


class CourseUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=80)
    grade: str | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> "CourseUpdate":
        for name in ("subject", "grade", "is_active"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class CourseOut(BaseModel):
    id: UUID
    subject: str
    grade: str
    is_active: bool
    batch_count: int = 0


class ScheduleIn(BaseModel):
    weekday: int = Field(ge=0, le=6)
    start_time: str = Field(pattern=_TIME_PATTERN)
    end_time: str = Field(pattern=_TIME_PATTERN)
    location: str | None = Field(default=None, max_length=200)
    meeting_link: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def end_after_start(self) -> "ScheduleIn":
        # Both times are zero-padded HH:MM (enforced by the pattern), so string comparison is valid.
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ScheduleOut(BaseModel):
    weekday: int
    start_time: str
    end_time: str
    location: str | None = None
    meeting_link: str | None = None


class BatchIn(BaseModel):
    course_id: UUID
    name: str = Field(min_length=1, max_length=120)
    monthly_fee_paise: int = Field(ge=0)
    capacity: int = Field(gt=0)
    teaching_mode: TeachingMode
    status: BatchStatus = "active"
    schedules: list[ScheduleIn] = Field(default_factory=list)


class BatchUpdate(BaseModel):
    course_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    monthly_fee_paise: int | None = Field(default=None, ge=0)
    capacity: int | None = Field(default=None, gt=0)
    teaching_mode: TeachingMode | None = None
    status: BatchStatus | None = None
    schedules: list[ScheduleIn] | None = None

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> "BatchUpdate":
        for name in (
            "course_id",
            "name",
            "monthly_fee_paise",
            "capacity",
            "teaching_mode",
            "status",
            "schedules",
        ):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class BatchOut(BaseModel):
    id: UUID
    course_id: UUID
    course_label: str
    name: str
    monthly_fee_paise: int
    capacity: int
    enrolled_count: int
    seats_left: int
    teaching_mode: TeachingMode
    status: BatchStatus
    schedules: list[ScheduleOut] = Field(default_factory=list)


class EnrollmentRequestIn(BaseModel):
    student_id: UUID
    batch_id: UUID


class EnrollmentOut(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str
    batch_id: UUID
    batch_name: str
    status: EnrollmentStatus
    requested_at: datetime
    decided_at: datetime | None = None
