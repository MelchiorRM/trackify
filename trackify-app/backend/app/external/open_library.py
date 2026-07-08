import httpx

BASE_URL = "https://openlibrary.org"


async def search_books(query: str, limit: int = 20) -> list[dict]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/search.json", params={"q": query, "limit": limit})
        resp.raise_for_status()
        return resp.json().get("docs", [])


async def get_work(olid: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/works/{olid}.json")
        resp.raise_for_status()
        return resp.json()


def _olid_from_key(key: str | None) -> str | None:
    return key.rsplit("/", 1)[-1] if key else None


def normalize_search_result(raw: dict) -> dict:
    olid = _olid_from_key(raw.get("key"))
    cover_id = raw.get("cover_i")
    return {
        "external_id": olid,
        "domain": "book",
        "title": raw.get("title"),
        "creator": ", ".join(raw.get("author_name", [])) or None,
        "year": raw.get("first_publish_year"),
        "genres": raw.get("subject", [])[:5],
        "overview": None,  # search.json doesn't carry a description — filled on detail fetch
        "cover_url": f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else None,
        "external_url": f"https://openlibrary.org/works/{olid}" if olid else None,
        "popularity": raw.get("edition_count"),
    }


def normalize_detail(raw: dict, olid: str) -> dict:
    description = raw.get("description")
    if isinstance(description, dict):
        description = description.get("value")
    return {
        "external_id": olid,
        "domain": "book",
        "title": raw.get("title"),
        "creator": None,  # works.json doesn't inline author names — left for the search result to supply
        "year": None,
        "genres": raw.get("subjects", [])[:5],
        "overview": description,
        "cover_url": f"https://covers.openlibrary.org/b/id/{raw['covers'][0]}-M.jpg" if raw.get("covers") else None,
        "external_url": f"https://openlibrary.org/works/{olid}",
        "popularity": None,
    }
