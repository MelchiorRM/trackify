import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.like import Like
from ..models.user import User
from . import notification_service, social_service
from .pagination import paginate, parse_cursor


async def create_like(db: AsyncSession, current_user: User, target_type: str, target_id: uuid.UUID) -> Like:
    target = await social_service.get_visible_target(db, current_user, target_type, target_id)

    existing = await db.execute(
        select(Like).where(
            Like.user_id == current_user.id, Like.target_type == target_type, Like.target_id == target_id
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already liked")

    like = Like(user_id=current_user.id, target_type=target_type, target_id=target_id)
    db.add(like)
    try:
        await db.flush()
    except IntegrityError:
        # Two concurrent likes for the same (user, target) race past the
        # SELECT check above; the unique constraint is the real guard.
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Already liked")
    like.user = current_user

    if target.user_id != current_user.id:
        await notification_service.create_notification(
            db,
            user_id=target.user_id,
            actor_id=current_user.id,
            type="like",
            target_type=target_type,
            target_id=target_id,
        )
    return like


async def delete_like(db: AsyncSession, current_user: User, target_type: str, target_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Like).where(
            Like.user_id == current_user.id, Like.target_type == target_type, Like.target_id == target_id
        )
    )
    like = result.scalar_one_or_none()
    if like is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Like not found")
    await db.delete(like)


async def list_likes(
    db: AsyncSession,
    current_user: User | None,
    target_type: str,
    target_id: uuid.UUID,
    cursor: str | None,
    limit: int,
) -> tuple[list[Like], str | None]:
    await social_service.get_visible_target(db, current_user, target_type, target_id)

    query = select(Like).where(Like.target_type == target_type, Like.target_id == target_id)
    if cursor:
        query = query.where(Like.created_at < parse_cursor(cursor))
    query = query.order_by(Like.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    rows = result.scalars().all()
    return paginate(rows, limit, lambda like: like.created_at.isoformat())
