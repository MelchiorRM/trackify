import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.follow import Follow
from ..models.user import User
from . import notification_service
from .pagination import paginate, parse_cursor


async def follow_user(db: AsyncSession, current_user: User, target: User) -> Follow:
    if target.id == current_user.id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Cannot follow yourself")

    existing = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == target.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already following")

    follow = Follow(follower_id=current_user.id, following_id=target.id)
    db.add(follow)
    try:
        await db.flush()
    except IntegrityError:
        # Two concurrent follows of the same target race past the SELECT
        # check above; the composite primary key is the real guard.
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Already following")

    await notification_service.create_notification(
        db,
        user_id=target.id,
        actor_id=current_user.id,
        type="follow",
        target_type="user",
        target_id=current_user.id,
    )
    return follow


async def unfollow_user(db: AsyncSession, current_user: User, target: User) -> None:
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.following_id == target.id)
    )
    follow = result.scalar_one_or_none()
    if follow is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not following")
    await db.delete(follow)


async def get_following_ids(db: AsyncSession, user: User) -> list[uuid.UUID]:
    result = await db.execute(select(Follow.following_id).where(Follow.follower_id == user.id))
    return list(result.scalars().all())


async def _list_follow_relation(
    db: AsyncSession, user: User, cursor: str | None, limit: int, *, self_col, other_col
) -> tuple[list[tuple[Follow, User]], str | None]:
    query = select(Follow, User).join(User, other_col == User.id).where(self_col == user.id)
    if cursor:
        query = query.where(Follow.created_at < parse_cursor(cursor))
    query = query.order_by(Follow.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    return paginate(result.all(), limit, lambda row: row[0].created_at.isoformat())


async def list_followers(
    db: AsyncSession, user: User, cursor: str | None, limit: int
) -> tuple[list[tuple[Follow, User]], str | None]:
    """Users who follow `user` — the Follow.follower_id side."""
    return await _list_follow_relation(
        db, user, cursor, limit, self_col=Follow.following_id, other_col=Follow.follower_id
    )


async def list_following(
    db: AsyncSession, user: User, cursor: str | None, limit: int
) -> tuple[list[tuple[Follow, User]], str | None]:
    """Users `user` follows — the Follow.following_id side."""
    return await _list_follow_relation(
        db, user, cursor, limit, self_col=Follow.follower_id, other_col=Follow.following_id
    )
