import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.repost import Repost
from ..models.user import User
from ..schemas.repost import RepostCreate, RepostRead
from ..services import repost_service

router = APIRouter(prefix="/reposts", tags=["reposts"])


@router.post("", response_model=RepostRead, status_code=status.HTTP_201_CREATED)
async def create_repost(
    body: RepostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Repost:
    repost = await repost_service.create_repost(
        db, current_user, body.target_type, body.target_id, body.comment
    )
    await db.commit()
    return repost


@router.delete("/{repost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repost(
    repost_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    repost = await repost_service.get_owned_repost(db, current_user, repost_id)
    await db.delete(repost)
    await db.commit()
