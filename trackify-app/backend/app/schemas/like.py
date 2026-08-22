import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .user import UserSummary

LikeTargetType = Literal["review", "collection", "post"]


class LikeCreate(BaseModel):
    target_type: LikeTargetType
    target_id: uuid.UUID


class LikeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user: UserSummary
    target_type: str
    target_id: uuid.UUID
    created_at: datetime


class LikePage(BaseModel):
    items: list[LikeRead]
    next_cursor: str | None
