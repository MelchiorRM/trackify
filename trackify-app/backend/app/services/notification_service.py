import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.notification import Notification
from ..models.user import User
from .pagination import paginate, parse_cursor


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    actor_id: uuid.UUID,
    type: str,
    target_type: str | None = None,
    target_id: uuid.UUID | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id, actor_id=actor_id, type=type, target_type=target_type, target_id=target_id
    )
    db.add(notification)
    return notification


async def list_notifications(
    db: AsyncSession, current_user: User, unread_only: bool, cursor: str | None, limit: int
) -> tuple[list[Notification], str | None]:
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.read.is_(False))
    if cursor:
        query = query.where(Notification.created_at < parse_cursor(cursor))
    query = query.order_by(Notification.created_at.desc()).limit(limit + 1)

    result = await db.execute(query)
    return paginate(result.scalars().all(), limit, lambda n: n.created_at.isoformat())


async def get_unread_count(db: AsyncSession, current_user: User) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id, Notification.read.is_(False))
    )
    return result.scalar_one()
