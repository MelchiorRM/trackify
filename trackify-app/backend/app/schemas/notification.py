import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .user import UserSummary


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor: UserSummary
    type: str
    target_type: str | None
    target_id: uuid.UUID | None
    read: bool
    created_at: datetime


class NotificationPage(BaseModel):
    items: list[NotificationRead]
    next_cursor: str | None


class UnreadCount(BaseModel):
    count: int
