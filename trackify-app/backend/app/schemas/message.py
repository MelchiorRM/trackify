import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .user import UserSummary


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sender: UserSummary
    body: str
    created_at: datetime
    read_at: datetime | None


class MessagePage(BaseModel):
    items: list[MessageRead]
    next_cursor: str | None


class ConversationRead(BaseModel):
    id: uuid.UUID
    other_user: UserSummary
    last_message: MessageRead | None
    unread_count: int
    created_at: datetime


class ConversationPage(BaseModel):
    items: list[ConversationRead]
    next_cursor: str | None
