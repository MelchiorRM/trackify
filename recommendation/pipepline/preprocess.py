"""
preprocess.py
Cleans and normalises all three raw datasets into a unified schema:

  items.csv     — one row per media item (book / movie / track)
  users.csv     — one row per user (cross-domain, merged)
  interactions.csv — one row per user-item interaction

Unified item schema:
  item_id | domain | title | creator | year | genres | tags | description_text

interactions schema:
  user_id | item_id | domain | rating | timestamp
"""

import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent
RAW     = ROOT / "data" / "raw"
PROC    = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MOVIES  (MovieLens ml-latest-small)
# ══════════════════════════════════════════════════════════════════════════════
def process_movies() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Processing movies (MovieLens ml-latest-small)...")

    # movies.csv  →  movieId,title,genres   (title: "Movie Title (1999)", genres: genre|genre)
    movies_raw = pd.read_csv(RAW / "movies" / "ml-latest-small" / "movies.csv")

    raw_title = movies_raw["title"].fillna("")
    year = pd.to_numeric(raw_title.str.extract(r"\((\d{4})\)\s*$")[0], errors="coerce")
    title = raw_title.str.replace(r"\s*\(\d{4}\)\s*$", "", regex=True).str.strip()
    genres = (
        movies_raw["genres"].fillna("")
        .replace("(no genres listed)", "")
        .str.replace("|", ", ", regex=False)
    )

    movies_df = pd.DataFrame({
        "source_id": movies_raw["movieId"].astype(str),
        "title":     title,
        "year":      year,
        "genres":    genres,
    })
    movies_df = movies_df[movies_df["title"] != ""].reset_index(drop=True)

    # ratings.csv  →  userId,movieId,rating,timestamp
    ratings_raw = pd.read_csv(RAW / "movies" / "ml-latest-small" / "ratings.csv")
    ratings_df = pd.DataFrame({
        "source_user_id": ratings_raw["userId"].astype(str),
        "source_id":      ratings_raw["movieId"].astype(str),
        "rating":         ratings_raw["rating"].astype(float),
        "timestamp":      ratings_raw["timestamp"].astype(int),
    })

    logger.success(f"  Movies:  {len(movies_df):,} items | {len(ratings_df):,} ratings")
    return movies_df, ratings_df

# ══════════════════════════════════════════════════════════════════════════════
#  BOOKS  (goodbooks-10k)
# ══════════════════════════════════════════════════════════════════════════════
def process_books() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Processing books (goodbooks-10k)...")
    books = pd.read_csv(RAW / "books" / "books.csv", low_memory=False)
    ratings = pd.read_csv(RAW / "books" / "ratings.csv")
    book_tags = pd.read_csv(RAW / "books" / "book_tags.csv")
    tags = pd.read_csv(RAW / "books" / "tags.csv")

    # Join tags onto books
    tag_joined = book_tags.merge(tags, on="tag_id")
    # Top 5 tags per book by count
    top_tags = (
        tag_joined.sort_values("count", ascending=False)
        .groupby("goodreads_book_id")["tag_name"]
        .apply(lambda x: ", ".join(x.head(5)))
        .reset_index()
        .rename(columns={"tag_name": "tags"})
    )

    books = books.merge(top_tags, on="goodreads_book_id", how="left")
    books_df = pd.DataFrame({
        "source_id": books["book_id"].astype(str),
        "title":     books["title"].fillna(""),
        "creator":   books["authors"].fillna(""),
        "year":      pd.to_numeric(books["original_publication_year"], errors="coerce"),
        "genres":    "",           # goodbooks has no direct genre col — tags cover this
        "tags":      books["tags"].fillna(""),
    })
    books_df = books_df[books_df["title"] != ""].reset_index(drop=True)

    ratings_df = pd.DataFrame({
        "source_user_id": ratings["user_id"].astype(str),
        "source_id":      ratings["book_id"].astype(str),
        "rating":         ratings["rating"].astype(float),
        "timestamp":      0,
    })
    logger.success(f"  Books:   {len(books_df):,} items | {len(ratings_df):,} ratings")
    return books_df, ratings_df

# ══════════════════════════════════════════════════════════════════════════════
#  MUSIC  (Spotify track audio-features + synthetic persona-based interactions)
# ══════════════════════════════════════════════════════════════════════════════
def process_music() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Processing music (Spotify dataset)...")
    tracks = pd.read_csv(RAW / "music" / "spotify.csv")  # adjust filename

    ARTIST_GENRES = {
        # Hip-Hop
        "YG":"hip-hop","Drake":"hip-hop","Kendrick Lamar":"hip-hop",
        "J. Cole":"hip-hop","Nicki Minaj":"hip-hop","2 Chainz":"hip-hop",
        "Big Sean":"hip-hop","A$AP Rocky":"hip-hop","Travis Scott":"hip-hop",
        "Cardi B":"hip-hop","Lil Wayne":"hip-hop","Eminem":"hip-hop",
        "Jay-Z":"hip-hop","Kanye West":"hip-hop","Nas":"hip-hop",
        "Wu-Tang Clan":"hip-hop","OutKast":"hip-hop",
        # Pop
        "Taylor Swift":"pop","Ed Sheeran":"pop","Ariana Grande":"pop",
        "Beyoncé":"pop","Adele":"pop","Bruno Mars":"pop","Rihanna":"pop",
        "Katy Perry":"pop","Lady Gaga":"pop","Justin Bieber":"pop",
        "Michael Jackson":"pop","Madonna":"pop","Prince":"pop",
        # Rock
        "Radiohead":"alternative rock","Arctic Monkeys":"indie rock",
        "The Beatles":"classic rock","Led Zeppelin":"hard rock",
        "Pink Floyd":"progressive rock","Nirvana":"grunge",
        "Foo Fighters":"alternative rock","The Rolling Stones":"classic rock",
        "David Bowie":"art rock","Queen":"classic rock",
        "The Doors":"psychedelic rock","Jimi Hendrix":"blues rock",
        "U2":"alternative rock","Bruce Springsteen":"heartland rock",
        "Metallica":"heavy metal","Black Sabbath":"heavy metal",
        "Tool":"progressive metal","Opeth":"progressive metal",
        # Electronic
        "Daft Punk":"electronic house","Aphex Twin":"electronic IDM",
        "Boards of Canada":"ambient electronic","Massive Attack":"trip-hop",
        "Portishead":"trip-hop","Burial":"ambient dubstep",
        "Brian Eno":"ambient","Kraftwerk":"electronic synth",
        "The Chemical Brothers":"big beat electronic",
        # Jazz
        "Miles Davis":"jazz","John Coltrane":"jazz bebop",
        "Bill Evans":"jazz piano","Thelonious Monk":"jazz bebop",
        "Duke Ellington":"jazz big band","Herbie Hancock":"jazz fusion",
        "Charles Mingus":"jazz avant-garde",
        # Classical / Soundtrack
        "Hans Zimmer":"soundtrack orchestral cinematic",
        "John Williams":"soundtrack orchestral epic",
        "Ennio Morricone":"soundtrack cinematic orchestral",
        "Philip Glass":"classical minimalism",
        "Arvo Pärt":"classical minimalism ambient",
        "Ludwig van Beethoven":"classical romantic orchestral",
        "Johann Sebastian Bach":"classical baroque",
        "Frédéric Chopin":"classical romantic piano",
        # Soul / R&B
        "Marvin Gaye":"soul r&b","Aretha Franklin":"soul gospel",
        "Stevie Wonder":"soul funk","D'Angelo":"neo-soul",
        "Kendrick Lamar":"hip-hop conscious",
        # Folk / Indie
        "Bob Dylan":"folk rock","Bon Iver":"indie folk",
        "Fleet Foxes":"indie folk","Sufjan Stevens":"indie folk orchestral",
        "Nick Drake":"folk acoustic melancholic",
        # Post-Rock / World
        "Sigur Rós":"post-rock ambient atmospheric",
        "Godspeed You! Black Emperor":"post-rock cinematic",
        "Explosions in the Sky":"post-rock cinematic ambient",
        "Fela Kuti":"afrobeat world funk",
    }

    def infer_genre(row):
        genre = ARTIST_GENRES.get(row["artist_name"])
        if genre:
            return genre
        e = row.get("energy", 0.5)
        a = row.get("acousticness", 0.5)
        d = row.get("danceability", 0.5)
        i = row.get("instrumentalness", 0)
        s = row.get("speechiness", 0)
        if s > 0.33:              return "hip-hop spoken word"
        if i > 0.8:               return "instrumental ambient"
        if a > 0.7 and e < 0.4:  return "acoustic folk"
        if e > 0.8 and a < 0.1:  return "electronic rock"
        if d > 0.75 and e > 0.6: return "dance pop electronic"
        if e < 0.3 and a > 0.5:  return "acoustic calm"
        return "pop"

    def mood_tags(row):
        tags = []
        v = row.get("valence", 0.5)
        e = row.get("energy", 0.5)
        a = row.get("acousticness", 0.5)
        d = row.get("danceability", 0.5)
        i = row.get("instrumentalness", 0)
        t = row.get("tempo", 120)
        s = row.get("speechiness", 0)

        # Mood from valence
        if v < 0.25:        tags.append("dark melancholic sad brooding")
        elif v < 0.45:      tags.append("melancholic bittersweet emotional")
        elif v < 0.65:      tags.append("neutral contemplative")
        else:               tags.append("happy upbeat bright joyful positive")

        # Energy
        if e < 0.3:         tags.append("calm quiet peaceful soft")
        elif e < 0.6:       tags.append("moderate flowing")
        else:               tags.append("energetic intense powerful driving")

        # Texture
        if a > 0.7:         tags.append("acoustic organic warm intimate")
        elif a < 0.15:      tags.append("electronic produced synthetic")

        # Rhythm
        if d > 0.75:        tags.append("danceable rhythmic groove")

        # Vocals
        if i > 0.7:         tags.append("instrumental no vocals")
        if s > 0.33:        tags.append("rap spoken word vocal")

        # Pace
        if t < 70:          tags.append("slow ballad")
        elif t > 150:       tags.append("fast rapid")

        return " ".join(tags)

    tracks = tracks.dropna(subset=["track_name"])
    tracks = tracks.drop_duplicates(subset=["track_id"]).reset_index(drop=True)

    tracks["genre"]     = tracks.apply(infer_genre, axis=1)
    tracks["mood_text"] = tracks.apply(mood_tags, axis=1)

    tracks_df = pd.DataFrame({
        "source_id": tracks["track_id"].astype(str),
        "title":     tracks["track_name"].fillna(""),
        "creator":   tracks["artist_name"].fillna(""),
        "year":      None,   # Spotify dataset has no year column
        "genres":    tracks["genre"],
        "tags":      tracks["mood_text"],
    })

    tracks_df = tracks_df[tracks_df["title"] != ""].reset_index(drop=True)
    tracks_df["popularity"] = tracks["popularity"].fillna(0)

    # Spotify has no user_id column — interactions come from a separate, synthetic,
    # persona-based generator (see pipepline/generate_music_interactions.py) since real
    # listening data doesn't exist for this dataset.
    ratings_path = RAW / "music" / "ratings.csv"
    if ratings_path.exists():
        ratings = pd.read_csv(ratings_path)
        ratings_df = pd.DataFrame({
            "source_user_id": ratings["user_id"].astype(str),
            "source_id":      ratings["track_id"].astype(str),
            "rating":         ratings["rating"].astype(float),
            "timestamp":      ratings["timestamp"].astype(int),
        })
    else:
        logger.warning(
            "  No data/raw/music/ratings.csv — music will have no interactions. "
            "Run pipepline/generate_music_interactions.py first."
        )
        ratings_df = pd.DataFrame(columns=["source_user_id", "source_id", "rating", "timestamp"])

    logger.success(
        f"  Music: {len(tracks_df):,} tracks | {len(ratings_df):,} ratings | "
        f"{tracks['artist_name'].nunique():,} artists | "
        f"{tracks['genre'].nunique():,} inferred genres"
    )
    return tracks_df, ratings_df

# ══════════════════════════════════════════════════════════════════════════════
#  MERGE INTO UNIFIED SCHEMA
# ══════════════════════════════════════════════════════════════════════════════
def build_unified(
    movies_items, movies_ratings,
    books_items,  books_ratings,
    music_items,  music_ratings,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("Building unified schema...")

    def make_items(df, domain, offset):
        base = {
            "source_id": df["source_id"].astype(str),
            "domain":    domain,
            "title":     df["title"].fillna("").str.strip(),
            "creator":   df.get("creator", pd.Series([""] * len(df))).fillna(""),
            "year":      pd.to_numeric(df.get("year", pd.Series([None] * len(df))), errors="coerce"),
            "genres":    df.get("genres", pd.Series([""] * len(df))).fillna(""),
            "tags":      df.get("tags",   pd.Series([""] * len(df))).fillna(""),
        }
        out = pd.DataFrame(base).reset_index(drop=True)
        out["item_id"] = (out.index + offset).astype(int)
        # Build a rich text field for embedding
        out["text"] = (
            out["title"]   + " " +
            out["creator"] + " " +
            out["genres"]  + " " +
            out["tags"]
        ).str.strip()
        return out

    movie_offset = 1
    book_offset  = movie_offset + len(movies_items)
    music_offset = book_offset  + len(books_items)

    m_items = make_items(movies_items, "movie", movie_offset)
    b_items = make_items(books_items,  "book",  book_offset)
    s_items = make_items(music_items,  "music", music_offset)

    items = pd.concat([m_items, b_items, s_items], ignore_index=True)

    # Build source_id → item_id lookup per domain
    def build_lookup(df):
        return dict(zip(df["source_id"].astype(str), df["item_id"]))

    m_lookup = build_lookup(m_items)
    b_lookup = build_lookup(b_items)
    s_lookup = build_lookup(s_items)

    def make_interactions(ratings_df, lookup, domain, user_offset):
        r = ratings_df.copy()
        r["item_id"] = r["source_id"].astype(str).map(lookup)
        r = r.dropna(subset=["item_id"])
        r["item_id"] = r["item_id"].astype(int)
        r["domain"]  = domain
        # Namespace user IDs per domain to avoid collisions
        r["user_id"] = (r["source_user_id"].astype(str) + f"_{domain}")
        return r[["user_id", "item_id", "domain", "rating", "timestamp"]]

    interactions = pd.concat([
        make_interactions(movies_ratings, m_lookup, "movie", 0),
        make_interactions(books_ratings,  b_lookup, "book",  0),
        make_interactions(music_ratings,  s_lookup, "music", 0),
    ], ignore_index=True)

    # Remap user_ids to integers
    all_users = interactions["user_id"].unique()
    user_map  = {u: i+1 for i, u in enumerate(all_users)}
    interactions["user_id"] = interactions["user_id"].map(user_map)
    users = pd.DataFrame({
        "user_id":      list(user_map.values()),
        "source_user":  list(user_map.keys()),
        "domain":       [u.split("_")[-1] for u in user_map.keys()],
    })

    logger.success(
        f"  Unified: {len(items):,} items | "
        f"{len(interactions):,} interactions | "
        f"{len(users):,} users"
    )
    return items, interactions, users

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    m_items, m_ratings = process_movies()
    b_items, b_ratings = process_books()
    s_items, s_ratings = process_music()

    items, interactions, users = build_unified(
        m_items, m_ratings,
        b_items, b_ratings,
        s_items, s_ratings,
    )

    # Save
    items.to_csv(PROC / "items.csv", index=False)
    interactions.to_csv(PROC / "interactions.csv", index=False)
    users.to_csv(PROC / "users.csv", index=False)

    logger.success(f"\nSaved to {PROC}")
    print("\n── Domain breakdown ─────────────────────────────")
    print(items.groupby("domain")[["item_id"]].count().rename(columns={"item_id": "items"}))
    print("\n── Interaction breakdown ─────────────────────────")
    print(interactions.groupby("domain")[["item_id"]].count().rename(columns={"item_id": "interactions"}))
    print("\n── Sample items ──────────────────────────────────")
    for domain in ["movie", "book", "music"]:
        sample = items[items["domain"] == domain].sample(1).iloc[0]
        print(f"\n  [{domain.upper()}] {sample['title']}")
        print(f"    genres: {sample['genres']}")
        print(f"    tags:   {sample['tags'][:80]}")
        print(f"    text:   {sample['text'][:100]}")