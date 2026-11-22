import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

AttendanceStatus = Literal["present", "absent", "excused"]
SessionStatus = Literal["scheduled", "conducted", "cancelled"]
MilestoneStatus = Literal["pending", "in_progress", "completed"]


class AttendanceRecordIn(BaseModel):
    student_id: uuid.UUID
    status: AttendanceStatus


class AttendanceMarkIn(BaseModel):
    session_id: uuid.UUID
    records: list[AttendanceRecordIn]


class AttendanceRecordOut(BaseModel):
    student_id: uuid.UUID
    student_name: str
    status: str


class AttendanceOut(BaseModel):
    session_id: uuid.UUID
    session_date: date
    batch_name: str
    records: list[AttendanceRecordOut]


class ClassSessionIn(BaseModel):
    batch_id: uuid.UUID
    session_date: date
    status: SessionStatus = "scheduled"


class ClassSessionStatusIn(BaseModel):
    status: SessionStatus


class ClassSessionOut(BaseModel):
    id: uuid.UUID
    batch_id: uuid.UUID
    batch_name: str
    session_date: date
    status: str


class StudentAttendanceRecordOut(BaseModel):
    session_date: date
    batch_name: str
    status: str


class StudentAttendanceSummaryOut(BaseModel):
    total: int
    present: int
    absent: int
    excused: int
    percent_present: int = Field(ge=0, le=100)
    records: list[StudentAttendanceRecordOut]


class MilestoneIn(BaseModel):
    student_id: uuid.UUID
    subject: str = Field(min_length=1, max_length=80)
    topic: str = Field(min_length=1, max_length=200)
    status: MilestoneStatus = "pending"
    score: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class MilestoneUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=80)
    topic: str | None = Field(default=None, min_length=1, max_length=200)
    status: MilestoneStatus | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None


class MilestoneOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    subject: str
    topic: str
    status: str
    score: int | None
    notes: str | None
    updated_at: datetime | None
