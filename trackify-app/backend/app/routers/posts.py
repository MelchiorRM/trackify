import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.post import Post
from ..models.user import User
from ..schemas.post import PostCreate, PostRead
from ..services import post_service

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Post:
    post = await post_service.create_post(db, current_user, body.body)
    await db.commit()
    return post


@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Post:
    return await post_service.get_post(db, post_id)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    post = await post_service.get_owned_post(db, current_user, post_id)
    await db.delete(post)
    await db.commit()
