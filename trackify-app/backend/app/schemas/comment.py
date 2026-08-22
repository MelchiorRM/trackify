import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .user import UserSummary

CommentTargetType = Literal["review", "post"]


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    user: UserSummary
    body: str
    created_at: datetime
    updated_at: datetime | None


class CommentPage(BaseModel):
    items: list[CommentRead]
    next_cursor: str | None
