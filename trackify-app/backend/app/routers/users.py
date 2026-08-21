import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.collection import Collection
from ..models.diary_entry import DiaryEntry
from ..models.favorite import Favorite
from ..models.media_item import MediaItem, UserLibrary
from ..models.review import Review
from ..models.user import User
from ..schemas.collection import CollectionRead
from ..schemas.diary_entry import DiaryEntryPage, DiaryEntryRead
from ..schemas.favorite import FavoriteRead, FavoritesUpdate
from ..schemas.library import LibraryRead
from ..schemas.review import ReviewRead
from ..schemas.user import PublicProfileRead, UserMe, UserUpdate
from ..services import library_service

router = APIRouter(prefix="/users", tags=["users"])


async def _get_user_by_username(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.get("/me", response_model=UserMe)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserMe)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    updates = body.model_dump(exclude_unset=True)

    new_value_clauses = [
        getattr(User, field) == value
        for field in ("username", "email")
        if (value := updates.get(field)) is not None
    ]
    if new_value_clauses:
        result = await db.execute(
            select(User).where(User.id != current_user.id, or_(*new_value_clauses))
        )
        if result.scalars().first() is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already in use")

    for field, value in updates.items():
        setattr(current_user, field, value)

    await db.commit()
    return current_user


@router.put("/me/favorites", response_model=list[FavoriteRead])
async def update_favorites(
    body: FavoritesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Favorite]:
    favorites = await library_service.set_favorites(db, current_user, body.item_ids)
    await db.commit()
    return favorites


@router.get("/{username}", response_model=PublicProfileRead)
async def get_public_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> PublicProfileRead:
    user = await _get_user_by_username(db, username)
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user.id).order_by(Favorite.position)
    )
    favorites = result.scalars().all()
    return PublicProfileRead(
        username=user.username,
        created_at=user.created_at,
        favorites=[FavoriteRead.model_validate(f) for f in favorites],
    )


@router.get("/{username}/library", response_model=list[LibraryRead])
async def get_user_library(
    username: str,
    domain: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[UserLibrary]:
    user = await _get_user_by_username(db, username)
    query = select(UserLibrary).join(MediaItem).where(UserLibrary.user_id == user.id)
    if domain:
        query = query.where(MediaItem.domain == domain)
    result = await db.execute(query.order_by(UserLibrary.added_at.desc()))
    return result.scalars().all()


@router.get("/{username}/reviews", response_model=list[ReviewRead])
async def get_user_reviews(
    username: str,
    db: AsyncSession = Depends(get_db),
) -> list[Review]:
    user = await _get_user_by_username(db, username)
    result = await db.execute(
        select(Review).where(Review.user_id == user.id).order_by(Review.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{username}/collections", response_model=list[CollectionRead])
async def get_user_collections(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Collection]:
    user = await _get_user_by_username(db, username)
    query = select(Collection).where(Collection.user_id == user.id)
    if user.id != current_user.id:
        query = query.where(Collection.is_public.is_(True))
    result = await db.execute(query.order_by(Collection.created_at.desc()))
    return result.scalars().unique().all()


@router.get("/{username}/diary", response_model=DiaryEntryPage)
async def get_user_diary(
    username: str,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
) -> DiaryEntryPage:
    user = await _get_user_by_username(db, username)
    query = select(DiaryEntry).where(DiaryEntry.user_id == user.id)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
        except ValueError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid cursor")
        query = query.where(DiaryEntry.created_at < cursor_dt)
    query = query.order_by(DiaryEntry.created_at.desc()).limit(limit + 1)

    result = await db.execute(query)
    rows = result.scalars().all()

    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = page[-1].created_at.isoformat() if has_more and page else None
    entries = [DiaryEntryRead.model_validate(entry) for entry in page]
    return DiaryEntryPage(entries=entries, next_cursor=next_cursor)
