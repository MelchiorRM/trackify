import asyncio
import time

import httpx

BASE_URL = "https://musicbrainz.org/ws/2"
USER_AGENT = "Trackify/0.1 (https://github.com/MelchiorRM/Trackify_repo)"

# MusicBrainz requires <=1 req/s. A module-level lock + last-call timestamp
# is enough for a single backend process; a multi-process deployment would
# need this enforced in Redis instead.
_last_call_at = 0.0
_lock = asyncio.Lock()


async def _throttle() -> None:
    global _last_call_at
    async with _lock:
        wait = 1.0 - (time.monotonic() - _last_call_at)
        if wait > 0:
            await asyncio.sleep(wait)
        _last_call_at = time.monotonic()


async def search_recordings(query: str, limit: int = 20) -> list[dict]:
    await _throttle()
    # MusicBrainz responses (esp. recordings with many linked releases) can
    # take much longer than typical REST APIs — 10s timed out repeatedly in
    # manual testing even on simple queries.
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{BASE_URL}/recording",
            params={"query": query, "limit": limit, "fmt": "json"},
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        return resp.json().get("recordings", [])


async def get_recording(mbid: str) -> dict:
    await _throttle()
    # MusicBrainz responses (esp. recordings with many linked releases) can
    # take much longer than typical REST APIs — 10s timed out repeatedly in
    # manual testing even on simple queries.
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{BASE_URL}/recording/{mbid}",
            params={"inc": "artist-credits", "fmt": "json"},
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        return resp.json()


def normalize_search_result(raw: dict) -> dict:
    artists = raw.get("artist-credit", [])
    release_date = raw.get("first-release-date")
    return {
        "external_id": raw.get("id"),
        "domain": "music",
        "title": raw.get("title"),
        "creator": ", ".join(a["name"] for a in artists) or None,
        "year": int(release_date[:4]) if release_date else None,
        "genres": [],  # needs a separate tag lookup MusicBrainz doesn't return inline
        "overview": None,
        "cover_url": None,  # Cover Art Archive needs a separate per-release request
        "external_url": f"https://musicbrainz.org/recording/{raw['id']}" if raw.get("id") else None,
        "popularity": raw.get("score"),
    }
