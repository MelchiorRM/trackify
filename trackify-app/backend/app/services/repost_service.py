import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.repost import Repost
from ..models.user import User
from . import notification_service, social_service


async def create_repost(
    db: AsyncSession, current_user: User, target_type: str, target_id: uuid.UUID, comment: str | None
) -> Repost:
    target = await social_service.get_visible_target(db, current_user, target_type, target_id)

    existing = await db.execute(
        select(Repost).where(
            Repost.user_id == current_user.id, Repost.target_type == target_type, Repost.target_id == target_id
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already reposted")

    repost = Repost(user_id=current_user.id, target_type=target_type, target_id=target_id, comment=comment)
    db.add(repost)
    try:
        await db.flush()
    except IntegrityError:
        # Two concurrent reposts for the same (user, target) race past the
        # SELECT check above; the unique constraint is the real guard.
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Already reposted")
    repost.user = current_user

    if target.user_id != current_user.id:
        await notification_service.create_notification(
            db,
            user_id=target.user_id,
            actor_id=current_user.id,
            type="repost",
            target_type=target_type,
            target_id=target_id,
        )
    return repost


async def get_owned_repost(db: AsyncSession, current_user: User, repost_id: uuid.UUID) -> Repost:
    result = await db.execute(
        select(Repost).where(Repost.id == repost_id, Repost.user_id == current_user.id)
    )
    repost = result.scalar_one_or_none()
    if repost is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repost not found")
    return repost
