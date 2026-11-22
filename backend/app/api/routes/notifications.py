import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.system import Notification
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    link: str | None
    is_read: bool
    created_at: datetime | None


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    unread_count: int


def _to_out(item: Notification) -> NotificationOut:
    return NotificationOut(
        id=item.id,
        title=item.title,
        body=item.body,
        link=item.link,
        is_read=item.is_read,
        created_at=item.created_at,
    )


@router.get("", response_model=NotificationListOut)
def list_notifications(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListOut:
    items = list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        ).all()
    )
    unread = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.is_read.is_(False),
        )
    ) or 0
    return NotificationListOut(items=[_to_out(n) for n in items], unread_count=int(unread))


@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationOut:
    item = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return _to_out(item)
