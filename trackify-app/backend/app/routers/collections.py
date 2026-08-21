import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db, get_redis
from ..models.collection import Collection, CollectionItem
from ..models.user import User
from ..schemas.collection import (
    CollectionCreate,
    CollectionItemCreate,
    CollectionItemRead,
    CollectionRead,
    CollectionUpdate,
)
from ..services import search_service

router = APIRouter(prefix="/collections", tags=["collections"])


async def _get_visible_collection(db: AsyncSession, current_user: User, collection_id: uuid.UUID) -> Collection:
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collection not found")
    if not collection.is_public and collection.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collection not found")
    return collection


async def _get_owned_collection(db: AsyncSession, current_user: User, collection_id: uuid.UUID) -> Collection:
    result = await db.execute(
        select(Collection).where(Collection.id == collection_id, Collection.user_id == current_user.id)
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collection not found")
    return collection


@router.get("", response_model=list[CollectionRead])
async def list_collections(
    user_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Collection]:
    query = select(Collection)
    if user_id == current_user.id:
        query = query.where(Collection.user_id == user_id)
    elif user_id is not None:
        query = query.where(Collection.user_id == user_id, Collection.is_public.is_(True))
    else:
        query = query.where(or_(Collection.is_public.is_(True), Collection.user_id == current_user.id))
    query = query.order_by(Collection.created_at.desc())

    result = await db.execute(query)
    return result.scalars().unique().all()


@router.post("", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
async def create_collection(
    body: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Collection:
    collection = Collection(user_id=current_user.id, **body.model_dump())
    db.add(collection)
    await db.commit()
    await db.refresh(collection, attribute_names=["items"])
    return collection


@router.get("/{collection_id}", response_model=CollectionRead)
async def get_collection(
    collection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Collection:
    return await _get_visible_collection(db, current_user, collection_id)


@router.patch("/{collection_id}", response_model=CollectionRead)
async def update_collection(
    collection_id: uuid.UUID,
    body: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Collection:
    collection = await _get_owned_collection(db, current_user, collection_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(collection, field, value)
    await db.commit()
    await db.refresh(collection, attribute_names=["items"])
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    collection = await _get_owned_collection(db, current_user, collection_id)
    await db.delete(collection)
    await db.commit()


@router.post("/{collection_id}/items", response_model=CollectionItemRead, status_code=status.HTTP_201_CREATED)
async def add_collection_item(
    collection_id: uuid.UUID,
    body: CollectionItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
) -> CollectionItem:
    await _get_owned_collection(db, current_user, collection_id)

    try:
        media_item = await search_service.get_or_create_media_item(
            db, redis_client, body.domain, body.external_id
        )
    except ValueError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{body.domain}/{body.external_id} not found")

    existing = await db.execute(
        select(CollectionItem).where(
            CollectionItem.collection_id == collection_id, CollectionItem.item_id == media_item.id
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Item already in this list")

    max_position = await db.execute(
        select(func.max(CollectionItem.position)).where(CollectionItem.collection_id == collection_id)
    )
    next_position = (max_position.scalar() or 0) + 1

    item = CollectionItem(
        collection_id=collection_id, item_id=media_item.id, position=next_position, note=body.note
    )
    db.add(item)
    await db.commit()
    await db.refresh(item, attribute_names=["item"])
    return item


@router.delete("/{collection_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_collection_item(
    collection_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_owned_collection(db, current_user, collection_id)

    result = await db.execute(
        select(CollectionItem).where(
            CollectionItem.collection_id == collection_id, CollectionItem.item_id == item_id
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not in this list")
    await db.delete(item)
    await db.commit()
