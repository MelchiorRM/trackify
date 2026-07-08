import asyncio
import json
import logging

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..external import musicbrainz, open_library, tmdb
from ..models.media_item import MediaItem
from . import cache_service

logger = logging.getLogger(__name__)

SEARCH_CACHE_TTL_SECONDS = 60 * 60  # 1 hour, per appPlan.txt SEARCH endpoint spec
FAILED_SEARCH_CACHE_TTL_SECONDS = 30  # short TTL when a provider failed, so a
# transient outage doesn't get cached as "no results" for a full hour
ITEM_CACHE_TTL_SECONDS = 60 * 60 * 24  # 24h, metadata doesn't change often


async def _search_movies(query: str, page: int) -> list[dict]:
    raw = await tmdb.search_movies(query, page=page)
    return [tmdb.normalize_search_result(r) for r in raw]


async def _search_books(query: str, page: int) -> list[dict]:
    # Open Library's search.json also takes a page param, but our client
    # doesn't forward it yet — first page only, same scope cut as music below.
    raw = await open_library.search_books(query)
    return [open_library.normalize_search_result(r) for r in raw]


async def _search_music(query: str, page: int) -> list[dict]:
    # MusicBrainz paginates via offset, not page — not wired up yet.
    raw = await musicbrainz.search_recordings(query)
    return [musicbrainz.normalize_search_result(r) for r in raw]


_SEARCHERS = {"movie": _search_movies, "book": _search_books, "music": _search_music}


async def _safe_search(domain: str, query: str, page: int) -> tuple[list[dict], bool]:
    """Returns (results, failed) — failed=True lets the caller use a short
    cache TTL instead of caching a transient outage as "no results" for an hour."""
    try:
        return await _SEARCHERS[domain](query, page), False
    except Exception:
        logger.warning("search provider failed for domain=%s", domain, exc_info=True)
        return [], True


async def search(redis_client: Redis, query: str, domain: str | None, page: int = 1) -> list[dict]:
    cache_key = f"search:{domain or 'all'}:{page}:{query.lower()}"
    cached = await cache_service.get_value(redis_client, cache_key)
    if cached is not None:
        return json.loads(cached)

    domains = [domain] if domain else list(_SEARCHERS)
    outcomes = await asyncio.gather(*(_safe_search(d, query, page) for d in domains))
    results = [r for batch, _ in outcomes for r in batch]
    any_failed = any(failed for _, failed in outcomes)

    ttl = FAILED_SEARCH_CACHE_TTL_SECONDS if any_failed else SEARCH_CACHE_TTL_SECONDS
    await cache_service.set_value(redis_client, cache_key, json.dumps(results), ttl)
    return results


async def fetch_item_detail(domain: str, external_id: str) -> dict | None:
    """Fetch a single item's full metadata directly from its provider, bypassing search."""
    try:
        if domain == "movie":
            return tmdb.normalize_detail(await tmdb.get_movie(external_id))
        if domain == "book":
            return open_library.normalize_detail(await open_library.get_work(external_id), external_id)
        if domain == "music":
            return musicbrainz.normalize_search_result(await musicbrainz.get_recording(external_id))
    except Exception:
        logger.warning("detail fetch failed for domain=%s external_id=%s", domain, external_id, exc_info=True)
    return None


async def get_or_create_media_item(db: AsyncSession, redis_client: Redis, domain: str, external_id: str) -> MediaItem:
    result = await db.execute(
        select(MediaItem).where(MediaItem.domain == domain, MediaItem.external_id == external_id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    cache_key = f"item:{domain}:{external_id}"
    cached = await cache_service.get_value(redis_client, cache_key)
    detail = json.loads(cached) if cached is not None else await fetch_item_detail(domain, external_id)
    if detail is None:
        raise ValueError(f"{domain}/{external_id} not found")
    if cached is None:
        await cache_service.set_value(redis_client, cache_key, json.dumps(detail), ITEM_CACHE_TTL_SECONDS)

    item = MediaItem(
        domain=domain,
        external_id=external_id,
        title=detail["title"],
        creator=detail.get("creator"),
        year=detail.get("year"),
        genres=",".join(detail.get("genres", [])) or None,
        overview=detail.get("overview"),
        cover_url=detail.get("cover_url"),
        external_url=detail.get("external_url"),
        popularity=detail.get("popularity"),
    )
    db.add(item)
    await db.flush()
    return item
