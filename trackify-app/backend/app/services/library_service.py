from datetime import date, datetime, timezone

from ..models.diary_entry import DiaryEntry
from ..models.media_item import UserLibrary


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
