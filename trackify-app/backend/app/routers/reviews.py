import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.review import Review
from ..models.user import User
from ..schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter(prefix="/reviews", tags=["reviews"])


async def _get_owned_review(db: AsyncSession, current_user: User, review_id: uuid.UUID) -> Review:
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return review


@router.get("", response_model=list[ReviewRead])
async def list_reviews(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[Review]:
    result = await db.execute(select(Review).where(Review.item_id == item_id).order_by(Review.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Review:
    existing = await db.execute(
        select(Review).where(Review.user_id == current_user.id, Review.item_id == body.item_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You already reviewed this item")

    review = Review(user_id=current_user.id, **body.model_dump())
    db.add(review)
    await db.commit()
    return review


@router.patch("/{review_id}", response_model=ReviewRead)
async def update_review(
    review_id: uuid.UUID,
    body: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Review:
    review = await _get_owned_review(db, current_user, review_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(review, field, value)
    await db.commit()
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    review = await _get_owned_review(db, current_user, review_id)
    await db.delete(review)
    await db.commit()
