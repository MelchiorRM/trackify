import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db, get_redis
from ..models.media_item import MediaItem, UserLibrary
from ..models.user import User
from ..schemas.library import LibraryCreate, LibraryRead, LibraryUpdate
from ..services import library_service, search_service

router = APIRouter(prefix="/library", tags=["library"])

_SORT_COLUMNS = {
    "title": MediaItem.title,
    "year": MediaItem.year,
}


@router.get("", response_model=list[LibraryRead])
async def list_library(
    domain: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    sort: str = "added_at",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserLibrary]:
    query = select(UserLibrary).join(MediaItem).where(UserLibrary.user_id == current_user.id)
    if domain:
        query = query.where(MediaItem.domain == domain)
    if status_filter:
        query = query.where(UserLibrary.status == status_filter)

    order_column = _SORT_COLUMNS.get(sort, UserLibrary.added_at)
    query = query.order_by(order_column.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=LibraryRead, status_code=status.HTTP_201_CREATED)
async def add_to_library(
    body: LibraryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> UserLibrary:
    try:
        item = await search_service.get_or_create_media_item(db, redis_client, body.domain, body.external_id)
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{body.domain}/{body.external_id} not found")

    existing = await db.execute(
        select(UserLibrary).where(UserLibrary.user_id == current_user.id, UserLibrary.item_id == item.id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Already in your library")

    library = UserLibrary(user_id=current_user.id, item_id=item.id, status="want")
    db.add(library)
    await db.commit()
    await db.refresh(library, attribute_names=["item"])
    return library


@router.patch("/{library_id}", response_model=LibraryRead)
async def update_library_entry(
    library_id: uuid.UUID,
    body: LibraryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserLibrary:
    library = await library_service.get_owned_library_row(db, current_user, library_id)
    diary_entry = library_service.apply_updates(library, body.model_dump(exclude_unset=True))
    if diary_entry is not None:
        db.add(diary_entry)
    await db.commit()
    await db.refresh(library, attribute_names=["item"])
    return library


@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_library(
    library_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    library = await library_service.get_owned_library_row(db, current_user, library_id)
    await db.delete(library)
    await db.commit()
