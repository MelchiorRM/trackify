from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.user import UserMe, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


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
