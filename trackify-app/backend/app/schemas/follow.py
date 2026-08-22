from datetime import datetime

from pydantic import BaseModel

from .user import UserSummary


class FollowRead(BaseModel):
    user: UserSummary
    created_at: datetime


class FollowPage(BaseModel):
    items: list[FollowRead]
    next_cursor: str | None
