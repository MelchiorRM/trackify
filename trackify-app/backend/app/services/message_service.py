import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.conversation import Conversation
from ..models.message import Message
from ..models.user import User
from .pagination import paginate, parse_cursor


async def get_or_create_conversation(db: AsyncSession, current_user: User, other: User) -> Conversation:
    if other.id == current_user.id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Cannot message yourself")

    user_one_id, user_two_id = sorted([current_user.id, other.id])
    result = await db.execute(
        select(Conversation).where(
            Conversation.user_one_id == user_one_id, Conversation.user_two_id == user_two_id
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is not None:
        return conversation

    conversation = Conversation(user_one_id=user_one_id, user_two_id=user_two_id)
    db.add(conversation)
    try:
        await db.flush()
    except IntegrityError:
        # Two concurrent get-or-creates for the same pair race past the
        # SELECT check above; re-fetch the row the other request just
        # committed instead of erroring — "get or create" must stay
        # idempotent under concurrency.
        await db.rollback()
        result = await db.execute(
            select(Conversation).where(
                Conversation.user_one_id == user_one_id, Conversation.user_two_id == user_two_id
            )
        )
        return result.scalar_one()
    return conversation


async def get_owned_conversation(db: AsyncSession, current_user: User, conversation_id: uuid.UUID) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conversation = result.scalar_one_or_none()
    if conversation is None or current_user.id not in (conversation.user_one_id, conversation.user_two_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")
    return conversation


def other_user_id(conversation: Conversation, current_user: User) -> uuid.UUID:
    return conversation.user_two_id if conversation.user_one_id == current_user.id else conversation.user_one_id


async def send_message(db: AsyncSession, current_user: User, conversation: Conversation, body: str) -> Message:
    message = Message(conversation_id=conversation.id, sender_id=current_user.id, body=body)
    db.add(message)
    await db.flush()
    message.sender = current_user
    return message


async def list_messages(
    db: AsyncSession, conversation: Conversation, cursor: str | None, limit: int
) -> tuple[list[Message], str | None]:
    query = select(Message).where(Message.conversation_id == conversation.id)
    if cursor:
        query = query.where(Message.created_at < parse_cursor(cursor))
    query = query.order_by(Message.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    return paginate(result.scalars().all(), limit, lambda m: m.created_at.isoformat())


async def mark_conversation_read(db: AsyncSession, current_user: User, conversation: Conversation) -> None:
    result = await db.execute(
        select(Message).where(
            Message.conversation_id == conversation.id,
            Message.sender_id != current_user.id,
            Message.read_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    for message in result.scalars().all():
        message.read_at = now


async def list_conversations(
    db: AsyncSession, current_user: User, cursor: str | None, limit: int
) -> tuple[list[dict], str | None]:
    """Returns caller's conversations most-recently-active first, each
    annotated with its other participant, last message, and unread count.
    N+1 queries, bounded by `limit` (default page size 20) — acceptable
    for MVP scope, no precedent yet for a more optimized fan-out here."""
    last_message_subq = (
        select(Message.conversation_id, func.max(Message.created_at).label("last_at"))
        .group_by(Message.conversation_id)
        .subquery()
    )
    query = (
        select(Conversation, last_message_subq.c.last_at)
        .outerjoin(last_message_subq, Conversation.id == last_message_subq.c.conversation_id)
        .where(or_(Conversation.user_one_id == current_user.id, Conversation.user_two_id == current_user.id))
    )
    result = await db.execute(query)
    rows = result.all()

    def sort_key(row) -> datetime:
        conversation, last_at = row
        return last_at or conversation.created_at

    rows.sort(key=sort_key, reverse=True)

    if cursor:
        cursor_dt = parse_cursor(cursor)
        rows = [row for row in rows if sort_key(row) < cursor_dt]

    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = sort_key(page[-1]).isoformat() if has_more and page else None

    conversations = []
    for conversation, _ in page:
        other = await db.get(User, other_user_id(conversation, current_user))
        last_message_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_message = last_message_result.scalar_one_or_none()
        if last_message is not None:
            await db.refresh(last_message, attribute_names=["sender"])
        unread_result = await db.execute(
            select(func.count()).select_from(Message).where(
                Message.conversation_id == conversation.id,
                Message.sender_id != current_user.id,
                Message.read_at.is_(None),
            )
        )
        conversations.append(
            {
                "conversation": conversation,
                "other_user": other,
                "last_message": last_message,
                "unread_count": unread_result.scalar_one(),
            }
        )
    return conversations, next_cursor


async def get_unread_message_count(db: AsyncSession, current_user: User) -> int:
    query = (
        select(func.count())
        .select_from(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            or_(Conversation.user_one_id == current_user.id, Conversation.user_two_id == current_user.id),
            Message.sender_id != current_user.id,
            Message.read_at.is_(None),
        )
    )
    result = await db.execute(query)
    return result.scalar_one()
