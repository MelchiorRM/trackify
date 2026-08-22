import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.comment import Comment
from ..models.user import User
from ..schemas.comment import CommentCreate, CommentPage, CommentRead, CommentUpdate
from ..services import comment_service, mention_service

router = APIRouter(tags=["comments"])


@router.get("/reviews/{review_id}/comments", response_model=CommentPage)
async def list_review_comments(
    review_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
) -> CommentPage:
    return await _list_comments(db, "review", review_id, cursor, limit)


@router.post("/reviews/{review_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_review_comment(
    review_id: uuid.UUID,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Comment:
    return await _create_comment(db, current_user, "review", review_id, body)


@router.get("/posts/{post_id}/comments", response_model=CommentPage)
async def list_post_comments(
    post_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
) -> CommentPage:
    return await _list_comments(db, "post", post_id, cursor, limit)


@router.post("/posts/{post_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_post_comment(
    post_id: uuid.UUID,
    body: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Comment:
    return await _create_comment(db, current_user, "post", post_id, body)


@router.patch("/comments/{comment_id}", response_model=CommentRead)
async def update_comment(
    comment_id: uuid.UUID,
    body: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Comment:
    comment = await comment_service.get_owned_comment(db, current_user, comment_id)
    comment.body = body.body
    await mention_service.sync_mentions(
        db, source_type="comment", source_id=comment.id, author=current_user, body=comment.body
    )
    await db.commit()
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    comment = await comment_service.get_owned_comment(db, current_user, comment_id)
    await db.delete(comment)
    await db.commit()


async def _list_comments(
    db: AsyncSession, target_type: str, target_id: uuid.UUID, cursor: str | None, limit: int
) -> CommentPage:
    comments, next_cursor = await comment_service.list_comments(db, target_type, target_id, cursor, limit)
    return CommentPage(items=[CommentRead.model_validate(c) for c in comments], next_cursor=next_cursor)


async def _create_comment(
    db: AsyncSession, current_user: User, target_type: str, target_id: uuid.UUID, body: CommentCreate
) -> Comment:
    comment = await comment_service.create_comment(db, current_user, target_type, target_id, body.body)
    await db.commit()
    return comment
