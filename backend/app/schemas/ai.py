import uuid
from typing import Literal

from pydantic import BaseModel, Field

ReminderTone = Literal["friendly", "formal", "urgent", "whatsapp"]


class ReminderIn(BaseModel):
    invoice_id: uuid.UUID
    tone: ReminderTone


class ReminderOut(BaseModel):
    text: str
    source: Literal["ai", "template"]


class CashExplainOut(BaseModel):
    text: str
    source: Literal["ai", "template"]


class AssistantIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AssistantOut(BaseModel):
    answer: str
    source: Literal["ai", "template"]
