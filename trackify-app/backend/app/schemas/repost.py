import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .user import UserSummary

RepostTargetType = Literal["review", "collection", "post"]


class RepostCreate(BaseModel):
    target_type: RepostTargetType
    target_id: uuid.UUID
    comment: str | None = Field(default=None, max_length=500)


class RepostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user: UserSummary
    target_type: str
    target_id: uuid.UUID
    comment: str | None
    created_at: datetime


class RepostPage(BaseModel):
    items: list[RepostRead]
    next_cursor: str | None
