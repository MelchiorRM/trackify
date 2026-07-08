from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db, get_redis
from ..models.user import User
from ..schemas.media_item import MediaItemRead
from ..services import search_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/{domain}/{external_id}", response_model=MediaItemRead)
async def get_item(
    domain: str,
    external_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> MediaItemRead:
    if domain not in ("movie", "book", "music"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown domain")

    try:
        item = await search_service.get_or_create_media_item(db, redis_client, domain, external_id)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{domain}/{external_id} not found")

    await db.commit()
    return item
