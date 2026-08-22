from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .user import UserSummary


class FeedItem(BaseModel):
    id: str  # stable per-source id (e.g. "review:<uuid>") — use as the React key
    type: str  # 'library' | 'review' | 'collection' | 'post' | 'follow' |
    # 'like' | 'comment' | 'repost'
    actor: UserSummary
    created_at: datetime
    data: dict[str, Any]


class FeedPage(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None
