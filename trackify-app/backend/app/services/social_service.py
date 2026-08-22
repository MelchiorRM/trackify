import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.collection import Collection
from ..models.post import Post
from ..models.review import Review
from ..models.user import User

_TARGET_MODELS = {"review": Review, "collection": Collection, "post": Post}


async def get_visible_target(
    db: AsyncSession, current_user: User | None, target_type: str, target_id: uuid.UUID
) -> Review | Collection | Post:
    """Fetches a like/comment/repost/mention target, 404ing if it doesn't
    exist or (for a private collection) isn't visible to current_user.
    Reviews and posts have no privacy concept, so they're always visible.
    current_user may be None (an anonymous viewer of a public target) — a
    private collection always 404s for them, same as for any other non-owner.
    """
    model = _TARGET_MODELS.get(target_type)
    if model is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unknown target_type: {target_type}")

    result = await db.execute(select(model).where(model.id == target_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{target_type.capitalize()} not found")
    if target_type == "collection" and not target.is_public and (
        current_user is None or target.user_id != current_user.id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Collection not found")
    return target
