import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .user import UserSummary


class PostCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)


class PostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user: UserSummary
    body: str
    created_at: datetime
    updated_at: datetime | None


class PostPage(BaseModel):
    items: list[PostRead]
    next_cursor: str | None
