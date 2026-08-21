import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.diary_entry import DiaryEntry
from ..models.favorite import Favorite
from ..models.media_item import MediaItem, UserLibrary
from ..models.user import User


async def get_owned_library_row(db: AsyncSession, current_user: User, library_id: uuid.UUID) -> UserLibrary:
    result = await db.execute(
        select(UserLibrary).where(UserLibrary.id == library_id, UserLibrary.user_id == current_user.id)
    )
    library = result.scalar_one_or_none()
    if library is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Library entry not found")
    return library


def log_diary_entry(
    library: UserLibrary,
    *,
    rewatch: bool,
    rating: float | None = None,
    note: str | None = None,
    logged_at: date | None = None,
) -> DiaryEntry:
    return DiaryEntry(
        user_id=library.user_id,
        item_id=library.item_id,
        library_id=library.id,
        logged_at=logged_at or date.today(),
        rewatch=rewatch,
        rating=rating,
        note=note,
    )


def apply_updates(library: UserLibrary, updates: dict) -> DiaryEntry | None:
    """Applies a PATCH /library/{id} body in place. Returns a diary entry to
    add to the session if completing the item should auto-log one."""
    now = datetime.now(timezone.utc)
    new_diary_entry = None

    new_status = updates.get("status")
    if new_status and new_status != library.status:
        if new_status == "in_progress" and library.started_at is None:
            library.started_at = now
        if new_status == "completed":
            library.completed_at = now
            new_diary_entry = log_diary_entry(library, rewatch=False)
        library.status = new_status

    if updates.get("progress") is not None:
        library.progress = updates["progress"]
    if updates.get("progress_total") is not None:
        library.progress_total = updates["progress_total"]

    return new_diary_entry


async def set_favorites(db: AsyncSession, user: User, item_ids: list[uuid.UUID]) -> list[Favorite]:
    """Replaces the caller's favorites with the given ordered set (max 4,
    enforced by the schema's Field(max_length=4) and the favorites table's
    own CHECK constraint — this is the third, business-logic layer: it also
    rejects duplicate/unknown item ids before touching the table."""
    if len(item_ids) != len(set(item_ids)):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Duplicate items in favorites")

    if item_ids:
        result = await db.execute(select(MediaItem.id).where(MediaItem.id.in_(item_ids)))
        found_ids = set(result.scalars().all())
        missing = [str(item_id) for item_id in item_ids if item_id not in found_ids]
        if missing:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown item(s): {', '.join(missing)}")

    await db.execute(delete(Favorite).where(Favorite.user_id == user.id))
    favorites = [
        Favorite(user_id=user.id, item_id=item_id, position=position)
        for position, item_id in enumerate(item_ids, start=1)
    ]
    db.add_all(favorites)
    await db.flush()
    for favorite in favorites:
        await db.refresh(favorite, attribute_names=["item"])
    return favorites
