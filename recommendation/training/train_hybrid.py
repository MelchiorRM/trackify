"""
train_hybrid.py

Phase 3 — hybrid ranking model combining Phase 1 (content/FAISS) and Phase 2
(collaborative/ALS) signals into one LightGBM ranker.

Features (the plan's original list, plus three additions for signals the
plan's own Tier 2/3 taxonomy calls out but the first pass omitted):
  content_similarity_score, collaborative_score, item_popularity,
  user_domain_affinity, creator_affinity, genre_affinity, recency_score,
  cross_domain_signal                                  — plan's original list
  quality_score    — mean received rating, normalised by domain rating scale.
                      Distinct from item_popularity (volume): a niche item with
                      a few 5-star ratings should rank differently from a
                      mass-popular average one. Maps to "Awards & critical
                      acclaim" (Tier 3).
  era_affinity      — user's preferred decade (weighted by their past ratings),
                      vs. recency_score's plain "how new is this." Maps to
                      "Era & Cultural period" (Tier 2).
  franchise_signal  — 1.0 if an item's normalised title also appears in a
                      DIFFERENT domain (e.g. "Dune" book + "Dune" movie), else
                      0.0. Maps to "Franchise & shared universe / Adaptations"
                      (Tier 3), which the plan calls the strongest hard link.

IMPORTANT — cross-domain caveat:
Movie, book, and music users are three disjoint populations in this dataset
(no real or synthetic person has interactions in more than one domain) — music
now has real (synthetic, see train_collaborative.py) interactions of its own,
but its users are a separate generated population, not movie/book users who
also happen to listen to music. That means there is still no genuine ground
truth for "would a movie user like this book/track" — every cross-domain
candidate would necessarily be labeled negative in training (the user can
never have a real positive cross-domain interaction here), which would just
teach the ranker to suppress cross-domain recommendations rather than learn
anything real.

So: the LightGBM ranker is trained and evaluated on SAME-DOMAIN candidates
only, where genuine held-out ratings exist (movie, book, music).
cross_domain_signal is computed as a feature for architectural completeness,
but during training it is always 0 (candidate domain == user domain), so the
model assigns it ~no weight. Actual cross-domain serving
(recommend_cross_domain below) uses a separate, explicitly
content-similarity-only path — the unified embedding space from Phase 1
already places all domains in one space, so this needs no extra learned
projection, but it is NOT validated by the ranker and should be read as a
heuristic demo, not an evaluated capability.

Outputs:
  models/hybrid_ranker.pkl   trained LightGBM LGBMRanker + feature column order
  models/user_vectors.npy    per-user content profile vectors (shared embedding space)
  models/user_vectors_ids.npy  matching user_id for each row above
"""

import pickle
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMRanker
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import evaluate_recommendations, temporal_holdout_per_user
from train_collaborative import encode, fit_als, filter_min_interactions, MIN_USER_INTERACTIONS, MIN_ITEM_INTERACTIONS

ROOT   = Path(__file__).resolve().parent.parent
PROC   = ROOT / "data" / "processed"
EMB    = ROOT / "embeddings"
RAW    = ROOT / "data" / "raw"
MODELS = ROOT / "models"

N_CONTENT_CANDIDATES = 100
N_ALS_CANDIDATES     = 100
N_RANDOM_NEGATIVES    = 50
MAX_TRAIN_USERS_PER_DOMAIN = 2000
K = 10
RATING_SCALE_MAX = {"movie": 5.0, "book": 5.0, "music": 5.0}
FEATURE_COLS = [
    "content_similarity_score", "collaborative_score", "item_popularity", "quality_score",
    "user_domain_affinity", "creator_affinity", "genre_affinity", "era_affinity",
    "recency_score", "franchise_signal", "cross_domain_signal",
]


# ── Global lookups ────────────────────────────────────────────────────────────
def load_globals():
    items = pd.read_csv(PROC / "items.csv")
    vectors = np.load(EMB / "item_vectors.npy")
    item_id_to_row = {iid: i for i, iid in enumerate(items["item_id"])}

    interactions = pd.read_csv(PROC / "interactions.csv")

    # Global item popularity in [0, 1]: log-scaled interaction count where available,
    # native Spotify popularity (0-100) for music, which has no interactions at all.
    counts = interactions.groupby("item_id").size()
    pop = np.log1p(counts)
    pop = (pop - pop.min()) / (pop.max() - pop.min())
    popularity = pop.to_dict()

    spotify = pd.read_csv(RAW / "music" / "spotify.csv")
    spotify_pop = dict(zip(spotify["track_id"].astype(str), spotify["popularity"] / 100.0))
    music_ids = items.loc[items["domain"] == "music", ["item_id", "source_id"]]
    for item_id, source_id in zip(music_ids["item_id"], music_ids["source_id"].astype(str)):
        if item_id not in popularity:
            popularity[item_id] = spotify_pop.get(source_id, 0.0)

    quality = build_quality_map(interactions, items)
    franchise = build_franchise_map(items)

    return items, vectors, item_id_to_row, interactions, popularity, quality, franchise


def year_bounds(items: pd.DataFrame) -> dict:
    return items.groupby("domain")["year"].agg(["min", "max"]).to_dict("index")


def build_quality_map(interactions: pd.DataFrame, items: pd.DataFrame) -> dict:
    """
    Mean received rating per item, normalised by the domain's rating scale —
    a "reception quality" signal distinct from item_popularity (which measures
    volume, not how well an item was received). Maps to the plan's "Awards &
    critical acclaim" tier. Domains with no interactions (music) have no such
    signal and default to a neutral 0.5 wherever this map is consulted.
    """
    domain_by_item = dict(zip(items["item_id"], items["domain"]))
    avg_rating = interactions.groupby("item_id")["rating"].mean()
    quality = {}
    for item_id, avg in avg_rating.items():
        scale = RATING_SCALE_MAX.get(domain_by_item.get(item_id), 5.0)
        quality[item_id] = float(avg / scale)
    return quality


def normalize_title(title) -> str:
    if pd.isna(title):
        return ""
    t = str(title).lower()
    t = re.sub(r"\(.*?\)", "", t)    # drop parenthetical (year, series tag)
    t = re.sub(r"[:\-,].*$", "", t)  # drop subtitle after colon/dash/comma
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return t.strip()


def build_franchise_map(items: pd.DataFrame) -> dict:
    """
    Item-level hard-link signal: 1.0 if this item's normalised title also
    appears in a DIFFERENT domain (e.g. "Dune" the book and "Dune" the movie),
    else 0.0. Maps to the plan's "Franchise & shared universe / Adaptations"
    tier — explicitly called out as the strongest cross-domain hard link.
    Exact match on normalised title (not fuzzy) to stay tractable at 150K items.
    """
    norm_titles = items["title"].map(normalize_title)
    title_domains: dict = {}
    for t, d in zip(norm_titles, items["domain"]):
        if t:
            title_domains.setdefault(t, set()).add(d)

    franchise = {}
    for item_id, t, d in zip(items["item_id"], norm_titles, items["domain"]):
        domains = title_domains.get(t, set())
        franchise[item_id] = 1.0 if domains - {d} else 0.0
    return franchise


# ── Per-user history summaries (for affinity features) ────────────────────────
def user_history_profiles(history_df: pd.DataFrame, items: pd.DataFrame) -> dict:
    """
    For each user, builds:
      creator_avg_rating: {creator: mean rating}
      genre_weight:       {genre: summed rating}, normalised by the user's max
      era_weight:         {decade: summed rating}, normalised by the user's max
                           (preferred-era match, distinct from raw item recency)
    """
    merged = history_df.merge(items[["item_id", "creator", "genres", "year"]], on="item_id", how="left")
    profiles = {}
    for user_id, group in merged.groupby("user_id"):
        creator_avg = group.groupby("creator")["rating"].mean().to_dict()

        genre_weight: dict = {}
        for genres, rating in zip(group["genres"], group["rating"]):
            for g in str(genres).split(","):
                g = g.strip()
                if g and g.lower() != "nan":
                    genre_weight[g] = genre_weight.get(g, 0.0) + rating
        max_w = max(genre_weight.values()) if genre_weight else 1.0
        genre_weight = {g: w / max_w for g, w in genre_weight.items()}

        era_weight: dict = {}
        for year, rating in zip(group["year"], group["rating"]):
            if pd.notna(year):
                decade = int(year // 10 * 10)
                era_weight[decade] = era_weight.get(decade, 0.0) + rating
        max_e = max(era_weight.values()) if era_weight else 1.0
        era_weight = {d: w / max_e for d, w in era_weight.items()}

        profiles[user_id] = {
            "creator_avg_rating": creator_avg,
            "genre_weight": genre_weight,
            "era_weight": era_weight,
        }
    return profiles


# ── Feature construction ──────────────────────────────────────────────────────
def build_features(
    user_id: int,
    user_domain: str,
    candidate_ids: list,
    profile_vector: np.ndarray,
    als_score_fn,
    items_by_id: pd.DataFrame,
    item_id_to_row: dict,
    vectors: np.ndarray,
    popularity: dict,
    quality: dict,
    franchise: dict,
    history_profile: dict,
    year_range: dict,
    user_domain_fracs: dict,
) -> pd.DataFrame:
    rows = []
    candidate_meta = items_by_id.loc[candidate_ids]
    creator_avg_rating = history_profile.get("creator_avg_rating", {})
    genre_weight = history_profile.get("genre_weight", {})
    era_weight = history_profile.get("era_weight", {})

    for item_id, meta in candidate_meta.iterrows():
        cand_domain = meta["domain"]
        cand_vec = vectors[item_id_to_row[item_id]]
        content_sim = float(np.dot(profile_vector, cand_vec))

        creator = meta.get("creator", "")
        creator_aff = creator_avg_rating.get(creator, 0.0) if isinstance(creator, str) and creator else 0.0

        raw_genres = meta.get("genres", "")
        cand_genres = [] if pd.isna(raw_genres) else [g.strip() for g in str(raw_genres).split(",") if g.strip()]
        genre_aff = float(np.mean([genre_weight.get(g, 0.0) for g in cand_genres])) if cand_genres else 0.0

        yr_info = year_range.get(cand_domain, {"min": None, "max": None})
        year = meta.get("year")
        if pd.notna(year) and yr_info["max"] not in (None,) and yr_info["max"] != yr_info["min"]:
            recency = (year - yr_info["min"]) / (yr_info["max"] - yr_info["min"])
        else:
            recency = 0.5  # neutral default when year is unavailable (e.g. music)

        era_aff = era_weight.get(int(year // 10 * 10), 0.0) if pd.notna(year) else 0.0

        rows.append({
            "item_id": item_id,
            "content_similarity_score": content_sim,
            "collaborative_score": als_score_fn(item_id) if cand_domain == user_domain else 0.0,
            "item_popularity": popularity.get(item_id, 0.0),
            "quality_score": quality.get(item_id, 0.5),
            "user_domain_affinity": user_domain_fracs.get(cand_domain, 0.0),
            "creator_affinity": creator_aff,
            "genre_affinity": genre_aff,
            "era_affinity": era_aff,
            "recency_score": recency,
            "franchise_signal": franchise.get(item_id, 0.0),
            "cross_domain_signal": content_sim if cand_domain != user_domain else 0.0,
        })
    return pd.DataFrame(rows)


# ── Training data construction (same-domain only — see module docstring) ──────
def build_training_examples(domain: str, items, vectors, item_id_to_row, interactions, popularity, quality, franchise, year_range):
    logger.info(f"── Building hybrid training examples: {domain.upper()} ──")
    domain_inter = interactions[interactions["domain"] == domain]
    filtered = filter_min_interactions(domain_inter, MIN_USER_INTERACTIONS, MIN_ITEM_INTERACTIONS)
    train_df, test_df = temporal_holdout_per_user(filtered, test_frac=0.2)

    # Leak-free feature ALS model: fit on the TRAIN split only (not the Phase 2 production
    # model, which was fit on all data and would leak test labels into these features).
    train_matrix, user_to_idx, item_to_idx, user_ids, item_ids = encode(train_df)
    als_model = fit_als(train_matrix)

    domain_mask = (items["domain"] == domain).to_numpy()
    domain_vectors = vectors[domain_mask]
    domain_item_ids = items.loc[domain_mask, "item_id"].to_numpy()
    domain_id_to_col = {iid: i for i, iid in enumerate(domain_item_ids)}
    items_by_id = items.set_index("item_id")

    test_users = test_df["user_id"].unique()
    if len(test_users) > MAX_TRAIN_USERS_PER_DOMAIN:
        test_users = np.random.default_rng(42).choice(test_users, size=MAX_TRAIN_USERS_PER_DOMAIN, replace=False)

    train_by_user = train_df.groupby("user_id")["item_id"].apply(set).to_dict()
    test_by_user  = test_df.groupby("user_id").apply(lambda g: dict(zip(g["item_id"], g["rating"]))).to_dict()
    history_profiles = user_history_profiles(train_df, items)
    rng = np.random.default_rng(7)

    all_rows = []
    for user_id in test_users:
        train_items = train_by_user.get(user_id, set())
        train_cols = [domain_id_to_col[i] for i in train_items if i in domain_id_to_col]
        if not train_cols:
            continue

        profile = domain_vectors[train_cols].mean(axis=0)
        norm = np.linalg.norm(profile)
        profile = profile / norm if norm > 0 else profile

        # Candidate generation: content top-N + ALS top-N (if user survived filtering) + actual
        # held-out positives (so the ranker has true positives to learn from) + random negatives.
        scores = domain_vectors @ profile
        scores[train_cols] = -np.inf
        content_top = np.argpartition(-scores, min(N_CONTENT_CANDIDATES, len(scores) - 1))[:N_CONTENT_CANDIDATES]
        candidates = set(domain_item_ids[content_top].tolist())

        if user_id in user_to_idx:
            als_ids, _ = als_model.recommend(
                user_to_idx[user_id], train_matrix[user_to_idx[user_id]], N=N_ALS_CANDIDATES, filter_already_liked_items=True
            )
            candidates.update(item_ids[c] for c in als_ids if c >= 0)

        test_items = test_by_user.get(user_id, {})
        candidates.update(test_items.keys())

        unseen_pool = np.setdiff1d(domain_item_ids, list(train_items | candidates), assume_unique=False)
        if len(unseen_pool) > 0:
            n_neg = min(N_RANDOM_NEGATIVES, len(unseen_pool))
            candidates.update(rng.choice(unseen_pool, size=n_neg, replace=False).tolist())

        def als_score_fn(item_id, _user_id=user_id, _col_map=item_to_idx):
            if _user_id not in user_to_idx or item_id not in _col_map:
                return 0.0
            return float(als_model.user_factors[user_to_idx[_user_id]] @ als_model.item_factors[_col_map[item_id]])

        feats = build_features(
            user_id, domain, list(candidates), profile, als_score_fn,
            items_by_id, item_id_to_row, vectors, popularity, quality, franchise,
            history_profiles.get(user_id, {}), year_range,
            user_domain_fracs={domain: 1.0},
        )
        feats["user_id"] = user_id
        # LightGBM's lambdarank objective requires integer graded relevance; *2 preserves
        # half-star (movie) precision as a 0-10 integer scale.
        feats["relevance"] = (feats["item_id"].map(test_items).fillna(0.0) * 2).round().astype(int)
        all_rows.append(feats)

    examples = pd.concat(all_rows, ignore_index=True)
    logger.success(f"  {len(examples):,} (user, candidate) examples from {len(all_rows):,} users")
    return examples


def train_ranker(examples: pd.DataFrame) -> tuple[LGBMRanker, dict]:
    examples = examples.sort_values("user_id").reset_index(drop=True)
    users = examples["user_id"].unique()
    rng = np.random.default_rng(42)
    eval_users = set(rng.choice(users, size=max(1, int(len(users) * 0.2)), replace=False))

    train_mask = ~examples["user_id"].isin(eval_users)
    train_ex, eval_ex = examples[train_mask], examples[~train_mask]

    def group_sizes(df):
        return df.groupby("user_id").size().to_numpy()

    model = LGBMRanker(objective="lambdarank", n_estimators=100, random_state=42, verbosity=-1)
    model.fit(
        train_ex[FEATURE_COLS], train_ex["relevance"],
        group=group_sizes(train_ex),
    )

    # Rank-based evaluation on the held-out users, compared against single-signal baselines
    def topk_by_score(df, score_col):
        recs = {}
        for user_id, group in df.groupby("user_id"):
            ranked = group.sort_values(score_col, ascending=False)["item_id"].tolist()
            recs[user_id] = ranked[:K]
        return recs

    eval_ex = eval_ex.copy()
    eval_ex["hybrid_score"] = model.predict(eval_ex[FEATURE_COLS])
    relevant_by_user = (
        eval_ex[eval_ex["relevance"] > 0].groupby("user_id")["item_id"].apply(set).to_dict()
    )

    results = {}
    for name, col in [
        ("hybrid", "hybrid_score"),
        ("content-only", "content_similarity_score"),
        ("collaborative-only", "collaborative_score"),
    ]:
        recs = topk_by_score(eval_ex, col)
        results[name] = evaluate_recommendations(recs, relevant_by_user, k=K)

    return model, results


# ── User profile vectors (for serving / cross-domain transfer) ────────────────
def build_user_vectors(interactions: pd.DataFrame, items: pd.DataFrame, vectors: np.ndarray, item_id_to_row: dict):
    user_ids, profile_vecs = [], []
    for user_id, group in interactions.groupby("user_id"):
        rows = [item_id_to_row[i] for i in group["item_id"] if i in item_id_to_row]
        if not rows:
            continue
        profile = vectors[rows].mean(axis=0)
        norm = np.linalg.norm(profile)
        profile = profile / norm if norm > 0 else profile
        user_ids.append(user_id)
        profile_vecs.append(profile)
    return np.array(user_ids), np.array(profile_vecs, dtype=np.float32)


# ── Cross-domain transfer demo (content-similarity only — see module docstring) ─
def recommend_cross_domain(user_id: int, target_domain: str, items, vectors, user_ids, user_vecs, k: int = 10):
    idx = np.where(user_ids == user_id)[0]
    if len(idx) == 0:
        raise ValueError(f"No profile vector for user {user_id}")
    profile = user_vecs[idx[0]]

    domain_mask = (items["domain"] == target_domain).to_numpy()
    domain_vectors = vectors[domain_mask]
    domain_items = items.loc[domain_mask].reset_index(drop=True)

    scores = domain_vectors @ profile
    top = np.argsort(-scores)[:k]
    return domain_items.iloc[top][["item_id", "title", "creator"]].assign(score=scores[top])


if __name__ == "__main__":
    items, vectors, item_id_to_row, interactions, popularity, quality, franchise = load_globals()
    year_range = year_bounds(items)

    examples = pd.concat([
        build_training_examples("movie", items, vectors, item_id_to_row, interactions, popularity, quality, franchise, year_range),
        build_training_examples("book", items, vectors, item_id_to_row, interactions, popularity, quality, franchise, year_range),
        build_training_examples("music", items, vectors, item_id_to_row, interactions, popularity, quality, franchise, year_range),
    ], ignore_index=True)

    model, results = train_ranker(examples)
    print("\n── Phase 3: hybrid ranker vs. single-signal baselines (held-out users) ──")
    for name, metrics in results.items():
        logger.success(
            f"  {name:<20} n_users={metrics['n_users']:,}  "
            f"Precision@10={metrics['precision@10']:.4f}  Recall@10={metrics['recall@10']:.4f}  "
            f"NDCG@10={metrics['ndcg@10']:.4f}  MAP@10={metrics['map@10']:.4f}"
        )

    print("\n── Feature importances (LightGBM, gain) ──")
    for col, imp in sorted(zip(FEATURE_COLS, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {col:<26} {imp}")

    with open(MODELS / "hybrid_ranker.pkl", "wb") as f:
        pickle.dump({"model": model, "feature_cols": FEATURE_COLS}, f)
    logger.success(f"Saved {MODELS / 'hybrid_ranker.pkl'}")

    user_ids, user_vecs = build_user_vectors(interactions, items, vectors, item_id_to_row)
    np.save(MODELS / "user_vectors.npy", user_vecs)
    np.save(MODELS / "user_vectors_ids.npy", user_ids)
    logger.success(f"Saved {MODELS / 'user_vectors.npy'} ({user_vecs.shape})")

    print("\n── Cross-domain transfer demo (content-similarity only, unvalidated) ──")
    sample_movie_user = interactions.loc[interactions["domain"] == "movie", "user_id"].sample(1, random_state=3).iloc[0]
    liked = interactions[(interactions["user_id"] == sample_movie_user) & (interactions["rating"] >= 4)]
    liked_titles = items.set_index("item_id").loc[liked["item_id"], "title"].tolist()
    print(f"\n  Movie user {sample_movie_user} liked: {liked_titles[:5]}")
    for target in ["book", "music"]:
        recs = recommend_cross_domain(sample_movie_user, target, items, vectors, user_ids, user_vecs, k=5)
        print(f"\n  → Recommended {target}s:")
        for _, row in recs.iterrows():
            print(f"      {row['title']:<50} ({row['creator']})  score={row['score']:.3f}")
