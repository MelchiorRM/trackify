import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.conversation import Conversation
from ..models.user import User
from ..models.message import Message
from ..schemas.message import (
    ConversationPage,
    ConversationRead,
    MessageCreate,
    MessagePage,
    MessageRead,
)
from ..schemas.notification import UnreadCount
from ..schemas.user import UserSummary
from ..services import message_service, user_service

router = APIRouter(tags=["messages"])


@router.post("/conversations/{username}", response_model=ConversationRead)
async def start_conversation(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationRead:
    other = await user_service.get_user_by_username(db, username)
    conversation = await message_service.get_or_create_conversation(db, current_user, other)
    await db.commit()
    return ConversationRead(
        id=conversation.id,
        other_user=UserSummary.model_validate(other),
        last_message=None,
        unread_count=0,
        created_at=conversation.created_at,
    )


@router.get("/conversations", response_model=ConversationPage)
async def list_conversations(
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationPage:
    rows, next_cursor = await message_service.list_conversations(db, current_user, cursor, limit)
    items = [
        ConversationRead(
            id=row["conversation"].id,
            other_user=UserSummary.model_validate(row["other_user"]),
            last_message=(
                MessageRead.model_validate(row["last_message"]) if row["last_message"] else None
            ),
            unread_count=row["unread_count"],
            created_at=row["conversation"].created_at,
        )
        for row in rows
    ]
    return ConversationPage(items=items, next_cursor=next_cursor)


@router.get("/conversations/{conversation_id}/messages", response_model=MessagePage)
async def list_messages(
    conversation_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessagePage:
    conversation = await message_service.get_owned_conversation(db, current_user, conversation_id)
    messages, next_cursor = await message_service.list_messages(db, conversation, cursor, limit)
    items = [MessageRead.model_validate(m) for m in messages]
    return MessagePage(items=items, next_cursor=next_cursor)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Message:
    conversation = await message_service.get_owned_conversation(db, current_user, conversation_id)
    message = await message_service.send_message(db, current_user, conversation, body.body)
    await db.commit()
    return message


@router.post("/conversations/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_conversation_read(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    conversation = await message_service.get_owned_conversation(db, current_user, conversation_id)
    await message_service.mark_conversation_read(db, current_user, conversation)
    await db.commit()


@router.get("/conversations/unread-count", response_model=UnreadCount)
async def get_unread_message_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UnreadCount:
    count = await message_service.get_unread_message_count(db, current_user)
    return UnreadCount(count=count)
