import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.post import Post
from ..models.user import User
from . import mention_service
from .pagination import paginate, parse_cursor


async def create_post(db: AsyncSession, current_user: User, body: str) -> Post:
    post = Post(id=uuid.uuid4(), user_id=current_user.id, body=body)
    db.add(post)
    await db.flush()
    post.user = current_user
    await mention_service.create_mentions(
        db, source_type="post", source_id=post.id, author=current_user, body=body
    )
    return post


async def get_post(db: AsyncSession, post_id: uuid.UUID) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post


async def get_owned_post(db: AsyncSession, current_user: User, post_id: uuid.UUID) -> Post:
    result = await db.execute(select(Post).where(Post.id == post_id, Post.user_id == current_user.id))
    post = result.scalar_one_or_none()
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return post


async def list_user_posts(
    db: AsyncSession, user: User, cursor: str | None, limit: int
) -> tuple[list[Post], str | None]:
    query = select(Post).where(Post.user_id == user.id)
    if cursor:
        query = query.where(Post.created_at < parse_cursor(cursor))
    query = query.order_by(Post.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    return paginate(result.scalars().all(), limit, lambda p: p.created_at.isoformat())
