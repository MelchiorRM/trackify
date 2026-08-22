from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.follow import Follow
from ..models.user import User
from ..schemas.feed import FeedItem, FeedPage
from ..schemas.follow import FollowPage, FollowRead
from ..schemas.user import UserSummary
from ..services import feed_service, follow_service, user_service

router = APIRouter(tags=["social"])


@router.post("/follows/{username}", response_model=FollowRead, status_code=status.HTTP_201_CREATED)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FollowRead:
    target = await user_service.get_user_by_username(db, username)
    follow = await follow_service.follow_user(db, current_user, target)
    await db.commit()
    return FollowRead(user=UserSummary.model_validate(target), created_at=follow.created_at)


@router.delete("/follows/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    target = await user_service.get_user_by_username(db, username)
    await follow_service.unfollow_user(db, current_user, target)
    await db.commit()


@router.get("/follows/followers", response_model=FollowPage)
async def list_followers(
    username: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FollowPage:
    user = await user_service.get_user_by_username(db, username) if username else current_user
    rows, next_cursor = await follow_service.list_followers(db, user, cursor, limit)
    items = [FollowRead(user=UserSummary.model_validate(u), created_at=f.created_at) for f, u in rows]
    return FollowPage(items=items, next_cursor=next_cursor)


@router.get("/follows/following", response_model=FollowPage)
async def list_following(
    username: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FollowPage:
    user = await user_service.get_user_by_username(db, username) if username else current_user
    rows, next_cursor = await follow_service.list_following(db, user, cursor, limit)
    items = [FollowRead(user=UserSummary.model_validate(u), created_at=f.created_at) for f, u in rows]
    return FollowPage(items=items, next_cursor=next_cursor)


@router.get("/feed", response_model=FeedPage)
async def get_feed(
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedPage:
    rows, next_cursor = await feed_service.get_feed(db, current_user, cursor, limit)
    items = [
        FeedItem(id=sort_id, type=type_, actor=UserSummary.model_validate(actor), created_at=created_at, data=data)
        for type_, actor, created_at, sort_id, data in rows
    ]
    return FeedPage(items=items, next_cursor=next_cursor)
