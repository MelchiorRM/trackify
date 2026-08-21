from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.stats import StatsRead
from ..services.stats_service import compute_stats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/me", response_model=StatsRead)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatsRead:
    return await compute_stats(db, current_user)
