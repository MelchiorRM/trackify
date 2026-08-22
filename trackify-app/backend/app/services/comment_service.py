import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.comment import Comment
from ..models.user import User
from . import mention_service, notification_service, social_service
from .pagination import paginate, parse_cursor


async def create_comment(
    db: AsyncSession, current_user: User, target_type: str, target_id: uuid.UUID, body: str
) -> Comment:
    target = await social_service.get_visible_target(db, current_user, target_type, target_id)

    comment = Comment(
        id=uuid.uuid4(), target_type=target_type, target_id=target_id, user_id=current_user.id, body=body
    )
    db.add(comment)
    await db.flush()
    comment.user = current_user

    if target.user_id != current_user.id:
        await notification_service.create_notification(
            db,
            user_id=target.user_id,
            actor_id=current_user.id,
            type="comment",
            target_type=target_type,
            target_id=target_id,
        )

    await mention_service.create_mentions(
        db, source_type="comment", source_id=comment.id, author=current_user, body=body
    )
    return comment


async def get_owned_comment(db: AsyncSession, current_user: User, comment_id: uuid.UUID) -> Comment:
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.user_id == current_user.id)
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return comment


async def list_comments(
    db: AsyncSession, target_type: str, target_id: uuid.UUID, cursor: str | None, limit: int
) -> tuple[list[Comment], str | None]:
    query = select(Comment).where(Comment.target_type == target_type, Comment.target_id == target_id)
    if cursor:
        query = query.where(Comment.created_at < parse_cursor(cursor))
    query = query.order_by(Comment.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    return paginate(result.scalars().all(), limit, lambda c: c.created_at.isoformat())
