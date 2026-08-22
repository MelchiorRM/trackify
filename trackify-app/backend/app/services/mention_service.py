import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.mention import Mention
from ..models.user import User
from . import notification_service

# Matches UserRegister.username's length constraint (min_length=3, max_length=32).
# (?<!\w) requires @ to start a mention (not be preceded by a word char), so
# "jane@example.com" doesn't false-positive-match "@example" as a mention.
MENTION_RE = re.compile(r"(?<!\w)@(\w{3,32})")


async def create_mentions(
    db: AsyncSession, *, source_type: str, source_id: uuid.UUID, author: User, body: str | None
) -> list[Mention]:
    if not body:
        return []

    usernames = set(MENTION_RE.findall(body))
    usernames.discard(author.username)
    if not usernames:
        return []

    result = await db.execute(select(User).where(User.username.in_(usernames)))
    mentioned_users = result.scalars().all()

    mentions = []
    for user in mentioned_users:
        mention = Mention(source_type=source_type, source_id=source_id, mentioned_user_id=user.id)
        db.add(mention)
        mentions.append(mention)
        await notification_service.create_notification(
            db,
            user_id=user.id,
            actor_id=author.id,
            type="mention",
            target_type=source_type,
            target_id=source_id,
        )
    return mentions


async def sync_mentions(
    db: AsyncSession, *, source_type: str, source_id: uuid.UUID, author: User, body: str | None
) -> None:
    """Reconciles mentions on an edited review/comment. Re-running
    create_mentions unconditionally on every edit would re-notify
    already-mentioned users and insert duplicate Mention rows each save
    (there's no uniqueness constraint to lean on) — so this only touches
    the difference: removes mentions for usernames no longer in the body,
    and creates (+ notifies) only newly added ones."""
    new_usernames = set(MENTION_RE.findall(body or ""))
    new_usernames.discard(author.username)

    result = await db.execute(
        select(Mention).where(Mention.source_type == source_type, Mention.source_id == source_id)
    )
    existing_by_user_id = {m.mentioned_user_id: m for m in result.scalars().all()}

    new_users_by_id = {}
    if new_usernames:
        result = await db.execute(select(User).where(User.username.in_(new_usernames)))
        new_users_by_id = {u.id: u for u in result.scalars().all()}

    for user_id, mention in existing_by_user_id.items():
        if user_id not in new_users_by_id:
            await db.delete(mention)

    for user_id, user in new_users_by_id.items():
        if user_id in existing_by_user_id:
            continue
        db.add(Mention(source_type=source_type, source_id=source_id, mentioned_user_id=user_id))
        await notification_service.create_notification(
            db,
            user_id=user_id,
            actor_id=author.id,
            type="mention",
            target_type=source_type,
            target_id=source_id,
        )
