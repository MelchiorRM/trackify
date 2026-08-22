import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ..models.collection import Collection
from ..models.comment import Comment
from ..models.follow import Follow
from ..models.like import Like
from ..models.media_item import MediaItem, UserLibrary
from ..models.post import Post
from ..models.repost import Repost
from ..models.review import Review
from ..models.user import User
from .follow_service import get_following_ids

_FeedRow = tuple[str, User, datetime, str, dict[str, Any]]  # (type, actor, created_at, sort_id, data)


def _parse_feed_cursor(cursor: str) -> tuple[datetime, str]:
    created_at_str, _, sort_id = cursor.partition("|")
    try:
        return datetime.fromisoformat(created_at_str), sort_id
    except ValueError:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid cursor")


async def _fetch_library_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    query = (
        select(UserLibrary, User)
        .join(User, UserLibrary.user_id == User.id)
        .where(UserLibrary.user_id.in_(user_ids))
    )
    if cursor_dt is not None:
        query = query.where(UserLibrary.added_at <= cursor_dt)
    query = query.order_by(UserLibrary.added_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for entry, actor in result.all():
        data = {
            "library_id": str(entry.id),
            "status": entry.status,
            "item_title": entry.item.title,
            "item_domain": entry.item.domain,
            "item_external_id": entry.item.external_id,
            "item_cover_url": entry.item.cover_url,
        }
        rows.append(("library", actor, entry.added_at, f"library:{entry.id}", data))
    return rows


async def _fetch_review_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    query = (
        select(Review, User, MediaItem)
        .join(User, Review.user_id == User.id)
        .join(MediaItem, Review.item_id == MediaItem.id)
        .where(Review.user_id.in_(user_ids))
    )
    if cursor_dt is not None:
        query = query.where(Review.created_at <= cursor_dt)
    query = query.order_by(Review.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for review, actor, item in result.all():
        data = {
            "review_id": str(review.id),
            "rating": review.rating,
            "body": review.body,
            "item_title": item.title,
            "item_domain": item.domain,
            "item_external_id": item.external_id,
        }
        rows.append(("review", actor, review.created_at, f"review:{review.id}", data))
    return rows


async def _fetch_collection_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    query = (
        select(Collection, User)
        .join(User, Collection.user_id == User.id)
        .where(Collection.user_id.in_(user_ids), Collection.is_public.is_(True))
    )
    if cursor_dt is not None:
        query = query.where(Collection.created_at <= cursor_dt)
    query = query.order_by(Collection.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for collection, actor in result.all():
        data = {
            "collection_id": str(collection.id),
            "name": collection.name,
            "description": collection.description,
            "item_count": len(collection.items),
        }
        rows.append(("collection", actor, collection.created_at, f"collection:{collection.id}", data))
    return rows


async def _fetch_post_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    query = select(Post).where(Post.user_id.in_(user_ids))
    if cursor_dt is not None:
        query = query.where(Post.created_at <= cursor_dt)
    query = query.order_by(Post.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for post in result.scalars().all():
        data = {"post_id": str(post.id), "body": post.body}
        rows.append(("post", post.user, post.created_at, f"post:{post.id}", data))
    return rows


async def _fetch_follow_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    Followee = aliased(User)
    query = (
        select(Follow, User, Followee)
        .join(User, Follow.follower_id == User.id)
        .join(Followee, Follow.following_id == Followee.id)
        .where(Follow.follower_id.in_(user_ids))
    )
    if cursor_dt is not None:
        query = query.where(Follow.created_at <= cursor_dt)
    query = query.order_by(Follow.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for follow, actor, followee in result.all():
        data = {"followed_username": followee.username, "followed_user_id": str(followee.id)}
        sort_id = f"follow:{follow.follower_id}:{follow.following_id}"
        rows.append(("follow", actor, follow.created_at, sort_id, data))
    return rows


async def _fetch_like_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    query = select(Like).where(Like.user_id.in_(user_ids))
    if cursor_dt is not None:
        query = query.where(Like.created_at <= cursor_dt)
    query = query.order_by(Like.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for like in result.scalars().all():
        data = {"target_type": like.target_type, "target_id": str(like.target_id)}
        rows.append(("like", like.user, like.created_at, f"like:{like.id}", data))
    return rows


async def _fetch_comment_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    query = select(Comment).where(Comment.user_id.in_(user_ids))
    if cursor_dt is not None:
        query = query.where(Comment.created_at <= cursor_dt)
    query = query.order_by(Comment.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for comment in result.scalars().all():
        data = {"target_type": comment.target_type, "target_id": str(comment.target_id), "body": comment.body}
        rows.append(("comment", comment.user, comment.created_at, f"comment:{comment.id}", data))
    return rows


async def _fetch_repost_rows(
    db: AsyncSession, user_ids: list[uuid.UUID], cursor_dt: datetime | None, limit: int
) -> list[_FeedRow]:
    query = select(Repost).where(Repost.user_id.in_(user_ids))
    if cursor_dt is not None:
        query = query.where(Repost.created_at <= cursor_dt)
    query = query.order_by(Repost.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = []
    for repost in result.scalars().all():
        data = {
            "target_type": repost.target_type,
            "target_id": str(repost.target_id),
            "comment": repost.comment,
        }
        rows.append(("repost", repost.user, repost.created_at, f"repost:{repost.id}", data))
    return rows


_SOURCES = (
    _fetch_library_rows,
    _fetch_review_rows,
    _fetch_collection_rows,
    _fetch_post_rows,
    _fetch_follow_rows,
    _fetch_like_rows,
    _fetch_comment_rows,
    _fetch_repost_rows,
)


async def get_feed(
    db: AsyncSession, user: User, cursor: str | None, limit: int
) -> tuple[list[_FeedRow], str | None]:
    """Merges 8 heterogeneous per-source queries (rather than one SQL UNION
    across differently-shaped tables) into a single cursor-paginated feed.
    Each source is over-fetched with a `created_at <= cursor_dt` filter (a
    safe superset), then the exact page boundary is trimmed in Python using
    a composite (created_at, sort_id) key, since ties on created_at across
    independent sources aren't resolvable by a single SQL ORDER BY.

    Each source query is itself capped at `limit + 1` rows: any row past a
    source's own top (limit + 1) can never land in the merged top (limit + 1)
    across all 8 sources, since that would require limit + 1 other rows
    already ranked above it — which, if they existed, would already be
    within its own source's cap. This keeps a feed page's cost bounded by
    limit regardless of how much total history the followed users have."""
    following_ids = await get_following_ids(db, user)
    if not following_ids:
        return [], None

    cursor_key: tuple[datetime, str] | None = _parse_feed_cursor(cursor) if cursor else None
    cursor_dt = cursor_key[0] if cursor_key else None

    all_rows: list[_FeedRow] = []
    for fetch in _SOURCES:
        all_rows.extend(await fetch(db, following_ids, cursor_dt, limit + 1))

    all_rows.sort(key=lambda row: (row[2], row[3]), reverse=True)

    if cursor_key is not None:
        all_rows = [row for row in all_rows if (row[2], row[3]) < cursor_key]

    has_more = len(all_rows) > limit
    page = all_rows[:limit]
    next_cursor = f"{page[-1][2].isoformat()}|{page[-1][3]}" if has_more and page else None
    return page, next_cursor
