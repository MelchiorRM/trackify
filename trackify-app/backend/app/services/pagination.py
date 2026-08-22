from datetime import datetime
from typing import Callable, Sequence, TypeVar

from fastapi import HTTPException, status

T = TypeVar("T")


def parse_cursor(cursor: str) -> datetime:
    """Shared cursor parser for the timestamp-cursor pagination style used
    across diary/comments/likes/reposts/notifications/messages/posts."""
    try:
        return datetime.fromisoformat(cursor)
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid cursor")


def paginate(rows: Sequence[T], limit: int, cursor_of: Callable[[T], str]) -> tuple[list[T], str | None]:
    """Trims a `limit + 1`-fetched row set to one page, deriving next_cursor
    from cursor_of(last_row) — shared by every list_* using this style."""
    has_more = len(rows) > limit
    page = list(rows[:limit])
    next_cursor = cursor_of(page[-1]) if has_more and page else None
    return page, next_cursor
