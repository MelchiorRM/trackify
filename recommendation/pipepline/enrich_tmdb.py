"""
enrich_tmdb.py

Enriches the unified movie items with metadata from TMDB: overview, director,
top cast, keywords, poster path, and TMDB's own rating/popularity signals.
Maps via links.csv (movieId -> tmdbId), since a movie's source_id in items.csv
is the MovieLens movieId.

API responses are cached to disk as raw JSON
(data/raw/movies/tmdb_cache/{tmdb_id}.json), so re-running only fetches what's
missing.

Updates data/processed/items.csv in place, for domain == "movie" rows:
  - creator  <- director (falls back to the existing value if none found)
  - genres   <- union of MovieLens genres and TMDB genres
  - tags     <- TMDB keywords + top cast
  - text     <- rebuilt to fold in the overview
  - new columns: overview, poster_path, vote_average, vote_count, popularity, release_date
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
RAW_MOVIES = ROOT / "data" / "raw" / "movies"
PROC       = ROOT / "data" / "processed"
CACHE_DIR  = RAW_MOVIES / "tmdb_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")
TMDB_TOKEN   = os.getenv("TMDB_TOKEN")
TMDB_API_KEY = os.getenv("TMBD_KEY") or os.getenv("TMDB_KEY")  # .env currently has the "TMBD_KEY" typo

if not TMDB_TOKEN and not TMDB_API_KEY:
    raise RuntimeError("No TMDB credentials found in .env (expected TMDB_TOKEN or TMBD_KEY).")

API_BASE    = "https://api.themoviedb.org/3"
MAX_WORKERS = 8
TIMEOUT     = 15
RETRIES     = 2


# ── TMDB client ───────────────────────────────────────────────────────────────
def _auth() -> tuple[dict, dict]:
    """Returns (params, headers). Prefers the v4 bearer token over the v3 key."""
    if TMDB_TOKEN:
        return {}, {"Authorization": f"Bearer {TMDB_TOKEN}", "accept": "application/json"}
    return {"api_key": TMDB_API_KEY}, {}


def fetch_movie(tmdb_id: int) -> dict | None:
    cache_file = CACHE_DIR / f"{tmdb_id}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())

    params, headers = _auth()
    params["append_to_response"] = "credits,keywords"

    for attempt in range(RETRIES + 1):
        try:
            resp = requests.get(f"{API_BASE}/movie/{tmdb_id}", params=params, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            cache_file.write_text(json.dumps(data))
            return data
        except requests.RequestException as e:
            if attempt == RETRIES:
                logger.warning(f"  tmdb_id={tmdb_id}: {e}")
                return None


def parse_movie(data: dict) -> dict:
    credits = data.get("credits", {})
    cast = [c["name"] for c in credits.get("cast", [])[:5]]
    director = next((c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"), "")
    keywords = [k["name"] for k in data.get("keywords", {}).get("keywords", [])]
    genres = [g["name"] for g in data.get("genres", [])]

    return {
        "overview":     (data.get("overview") or "").strip(),
        "tmdb_genres":  genres,
        "director":     director,
        "cast":         cast,
        "keywords":     keywords,
        "poster_path":  data.get("poster_path") or "",
        "vote_average": data.get("vote_average"),
        "vote_count":   data.get("vote_count"),
        "popularity":   data.get("popularity"),
        "release_date": data.get("release_date") or "",
    }


def fetch_all(movie_ids: pd.DataFrame) -> pd.DataFrame:
    """movie_ids: columns source_id (movieId, str) and tmdb_id (int)."""
    rows = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {
            pool.submit(fetch_movie, int(tmdb_id)): source_id
            for source_id, tmdb_id in zip(movie_ids["source_id"], movie_ids["tmdb_id"])
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="TMDB"):
            source_id = futures[future]
            data = future.result()
            if data is None:
                continue
            parsed = parse_movie(data)
            parsed["source_id"] = source_id
            rows.append(parsed)
    return pd.DataFrame(rows)


# ── Merge ─────────────────────────────────────────────────────────────────────
EXTRA_COLS = ["overview", "poster_path", "vote_average", "vote_count", "popularity", "release_date"]


def union_genres(row) -> str:
    raw = row["genres"]
    existing = [] if pd.isna(raw) else [g.strip() for g in str(raw).split(",") if g.strip()]
    tmdb = row["tmdb_genres"] if isinstance(row["tmdb_genres"], list) else []
    return ", ".join(dict.fromkeys(existing + tmdb))  # de-dup, keep order


def build_tags(row) -> str:
    keywords = row["keywords"] if isinstance(row["keywords"], list) else []
    cast = row["cast"] if isinstance(row["cast"], list) else []
    return ", ".join(keywords + cast)


def merge_into_items(items: pd.DataFrame, enriched: pd.DataFrame) -> pd.DataFrame:
    original_cols = list(items.columns)

    movies = items[items["domain"] == "movie"].copy()
    movies["source_id"] = movies["source_id"].astype(str)
    enriched = enriched.copy()
    enriched["source_id"] = enriched["source_id"].astype(str)

    movies = movies.merge(enriched, on="source_id", how="left")

    movies["genres"]  = movies.apply(union_genres, axis=1)
    movies["tags"]    = movies.apply(build_tags, axis=1)
    movies["creator"] = movies["director"].fillna(movies["creator"])
    movies["overview"] = movies["overview"].fillna("")
    movies["text"] = (
        movies["title"] + " " + movies["creator"].fillna("") + " " +
        movies["genres"] + " " + movies["tags"] + " " + movies["overview"]
    ).str.strip()

    movies = movies[[c for c in original_cols + EXTRA_COLS if c in movies.columns]]

    others = items[items["domain"] != "movie"].copy()
    for col in EXTRA_COLS:
        others[col] = ""

    return (
        pd.concat([movies, others], ignore_index=True)
        .sort_values("item_id")
        .reset_index(drop=True)
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    items = pd.read_csv(PROC / "items.csv")
    links = pd.read_csv(RAW_MOVIES / "ml-latest-small" / "links.csv")
    links["movieId"] = links["movieId"].astype(str)

    movie_ids = items.loc[items["domain"] == "movie", ["source_id"]].copy()
    movie_ids["source_id"] = movie_ids["source_id"].astype(str)
    movie_ids = movie_ids.merge(links[["movieId", "tmdbId"]], left_on="source_id", right_on="movieId")
    movie_ids = movie_ids.dropna(subset=["tmdbId"])
    movie_ids["tmdb_id"] = movie_ids["tmdbId"].astype(int)

    logger.info(f"Fetching TMDB metadata for {len(movie_ids):,} movies...")
    enriched = fetch_all(movie_ids[["source_id", "tmdb_id"]])
    logger.success(f"Fetched {len(enriched):,}/{len(movie_ids):,} movies from TMDB (cache + API)")

    items = merge_into_items(items, enriched)
    items.to_csv(PROC / "items.csv", index=False)
    logger.success(f"Updated {PROC / 'items.csv'}")

    print("\n── Sample enriched movies ──────────────────────────")
    sample = items[(items["domain"] == "movie") & (items["overview"] != "")].sample(3, random_state=1)
    for _, row in sample.iterrows():
        print(f"\n  {row['title']} ({str(row.get('release_date', ''))[:4]})")
        print(f"    creator: {row['creator']}")
        print(f"    genres:  {row['genres']}")
        print(f"    tags:    {str(row['tags'])[:80]}")
        print(f"    overview:{str(row['overview'])[:100]}")
