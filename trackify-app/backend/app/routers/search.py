from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis

from ..dependencies import get_current_user, get_redis
from ..models.user import User
from ..schemas.search import SearchResponse
from ..services import search_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(min_length=1),
    domain: str | None = Query(default=None, pattern="^(movie|book|music)$"),
    page: int = Query(default=1, ge=1),
    current_user: User = Depends(get_current_user),
    redis_client: Redis = Depends(get_redis),
) -> SearchResponse:
    results = await search_service.search(redis_client, q, domain, page)
    return SearchResponse(query=q, domain=domain, results=results)
