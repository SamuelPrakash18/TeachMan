"""Tutor analytics chat (authenticated) and stateless support chat (public).

Nothing in this module stores chat messages, logs message content, or writes
to the database. Figures come only from build_business_facts; the model never
computes them.
"""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import require_tutor
from app.api.routes.ai import _caller_business
from app.db.session import get_db
from app.models.user import User
from app.services.ai_service import build_business_facts, fallback_summary
from app.services.nvidia_client import chat_completion

router = APIRouter(prefix="/api", tags=["chat"])

ANALYTICS_SYSTEM_PROMPT = (
    "You are TeachMan's analytics assistant for a tutor. "
    "Answer only from the FACTS JSON below. "
    "Never invent amounts, dates, invoices or students. "
    "Amounts are integer paise: divide by 100 to show rupees. "
    "If the facts do not contain the answer, say so plainly. "
    "Keep answers short."
)

SUPPORT_SYSTEM_PROMPT = (
    "You are TeachMan Help, the support assistant for TeachMan, a financial back-office app "
    "for home tutors and tuition centres. Explain how to use TeachMan: tutor and parent "
    "registration, invoices, UPI payment claims that the tutor verifies, expenses, cash-flow "
    "forecast, the what-if simulator, notifications and account settings. You have NO access "
    "to any account or financial data: never state a balance, invoice or person's details, "
    "and never ask for passwords or OTPs. For account problems, tell the user to contact the "
    "TeachMan team through the support email configured by the operator. "
    "Keep answers under 120 words."
)

SUPPORT_UNAVAILABLE_TEXT = "The help assistant is unavailable right now. Please try again later."


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class ChatIn(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)

    @field_validator("messages")
    @classmethod
    def last_message_must_be_user(cls, messages: list[ChatMessage]) -> list[ChatMessage]:
        if messages[-1].role != "user":
            raise ValueError("the last message must have role 'user'")
        return messages


def _message_dicts(body: ChatIn) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in body.messages]


@router.post("/ai/analytics-chat")
def analytics_chat(
    body: ChatIn,
    user: User = Depends(require_tutor),
    db: Session = Depends(get_db),
) -> dict:
    business = _caller_business(db, user)
    facts = build_business_facts(db, business.id)
    system_prompt = ANALYTICS_SYSTEM_PROMPT + "\n\nFACTS: " + json.dumps(facts, default=str)

    reply = chat_completion([{"role": "system", "content": system_prompt}, *_message_dicts(body)])
    if reply:
        return {"reply": reply, "source": "ai"}
    return {"reply": fallback_summary(facts), "source": "template"}


@router.post("/support/chat")
def support_chat(body: ChatIn) -> dict:
    reply = chat_completion(
        [{"role": "system", "content": SUPPORT_SYSTEM_PROMPT}, *_message_dicts(body)]
    )
    if reply:
        return {"reply": reply, "source": "ai"}
    return {"reply": SUPPORT_UNAVAILABLE_TEXT, "source": "unavailable"}
