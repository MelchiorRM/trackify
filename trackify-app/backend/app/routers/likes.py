import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_current_user_optional, get_db
from ..models.like import Like
from ..models.user import User
from ..schemas.like import LikeCreate, LikePage, LikeRead
from ..services import like_service

router = APIRouter(prefix="/likes", tags=["likes"])


@router.post("", response_model=LikeRead, status_code=status.HTTP_201_CREATED)
async def create_like(
    body: LikeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Like:
    like = await like_service.create_like(db, current_user, body.target_type, body.target_id)
    await db.commit()
    return like


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_like(
    body: LikeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await like_service.delete_like(db, current_user, body.target_type, body.target_id)
    await db.commit()


@router.get("", response_model=LikePage)
async def list_likes(
    target_type: str,
    target_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> LikePage:
    likes, next_cursor = await like_service.list_likes(db, current_user, target_type, target_id, cursor, limit)
    return LikePage(items=[LikeRead.model_validate(like) for like in likes], next_cursor=next_cursor)
