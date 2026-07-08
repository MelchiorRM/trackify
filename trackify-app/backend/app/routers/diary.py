import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.diary_entry import DiaryEntry
from ..models.media_item import UserLibrary
from ..models.user import User
from ..schemas.diary_entry import DiaryEntryCreate, DiaryEntryRead
from ..services.library_service import log_diary_entry

router = APIRouter(tags=["diary"])


async def _get_owned_library_row(db: AsyncSession, current_user: User, library_id: uuid.UUID) -> UserLibrary:
    result = await db.execute(
        select(UserLibrary).where(UserLibrary.id == library_id, UserLibrary.user_id == current_user.id)
    )
    library = result.scalar_one_or_none()
    if library is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Library entry not found")
    return library


@router.get("/library/{library_id}/diary", response_model=list[DiaryEntryRead])
async def list_diary_entries(
    library_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DiaryEntry]:
    await _get_owned_library_row(db, current_user, library_id)
    result = await db.execute(
        select(DiaryEntry).where(DiaryEntry.library_id == library_id).order_by(DiaryEntry.logged_at.desc())
    )
    return result.scalars().all()


@router.post("/library/{library_id}/diary", response_model=DiaryEntryRead, status_code=status.HTTP_201_CREATED)
async def create_diary_entry(
    library_id: uuid.UUID,
    body: DiaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiaryEntry:
    library = await _get_owned_library_row(db, current_user, library_id)
    entry = log_diary_entry(
        library, rewatch=body.rewatch, rating=body.rating, note=body.note, logged_at=body.logged_at
    )
    db.add(entry)
    await db.commit()
    return entry


@router.delete("/diary/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diary_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(DiaryEntry).where(DiaryEntry.id == entry_id, DiaryEntry.user_id == current_user.id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Diary entry not found")
    await db.delete(entry)
    await db.commit()
