import httpx

from ..config import settings

BASE_URL = "https://api.themoviedb.org/3"

# TMDB's /search/movie response only carries genre_ids, not names — this
# table is the stable, rarely-changing official TMDB movie genre list, used
# so search doesn't need an extra round trip per result. Detail fetches use
# the full named genres from /movie/{id} instead.
GENRE_NAMES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy", 80: "Crime",
    99: "Documentary", 18: "Drama", 10751: "Family", 14: "Fantasy", 36: "History",
    27: "Horror", 10402: "Music", 9648: "Mystery", 10749: "Romance",
    878: "Science Fiction", 10770: "TV Movie", 53: "Thriller", 10752: "War",
    37: "Western",
}


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.tmdb_bearer_token}"} if settings.tmdb_bearer_token else {}


def _params(**extra) -> dict:
    params = {"api_key": settings.tmdb_api_key, **extra}
    return {k: v for k, v in params.items() if v not in (None, "")}


async def search_movies(query: str, page: int = 1) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/search/movie", params=_params(query=query, page=page), headers=_headers()
        )
        resp.raise_for_status()
        return resp.json().get("results", [])


async def get_movie(tmdb_id: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/movie/{tmdb_id}",
            params=_params(append_to_response="credits,keywords"),
            headers=_headers(),
        )
        resp.raise_for_status()
        return resp.json()


def normalize_search_result(raw: dict) -> dict:
    return {
        "external_id": str(raw["id"]),
        "domain": "movie",
        "title": raw.get("title") or raw.get("original_title"),
        "creator": None,  # director isn't in search results — needs /credits, filled on detail fetch
        "year": int(raw["release_date"][:4]) if raw.get("release_date") else None,
        "genres": [GENRE_NAMES[g] for g in raw.get("genre_ids", []) if g in GENRE_NAMES],
        "overview": raw.get("overview") or None,
        "cover_url": f"https://image.tmdb.org/t/p/w342{raw['poster_path']}" if raw.get("poster_path") else None,
        "external_url": f"https://www.themoviedb.org/movie/{raw['id']}",
        "popularity": raw.get("popularity"),
    }


def normalize_detail(raw: dict) -> dict:
    director = next(
        (c["name"] for c in raw.get("credits", {}).get("crew", []) if c.get("job") == "Director"), None
    )
    return {
        "external_id": str(raw["id"]),
        "domain": "movie",
        "title": raw.get("title") or raw.get("original_title"),
        "creator": director,
        "year": int(raw["release_date"][:4]) if raw.get("release_date") else None,
        "genres": [g["name"] for g in raw.get("genres", [])],
        "overview": raw.get("overview") or None,
        "cover_url": f"https://image.tmdb.org/t/p/w500{raw['poster_path']}" if raw.get("poster_path") else None,
        "external_url": f"https://www.themoviedb.org/movie/{raw['id']}",
        "popularity": raw.get("popularity"),
    }
