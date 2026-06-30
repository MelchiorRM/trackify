"""
generate_music_interactions.py

Spotify's track-features dataset (data/raw/music/spotify.csv) has no real
user data at all — no plays, no ratings. That leaves music as the only
domain with zero personalization, which is inconsistent with movies and
books (both have real explicit ratings). This generates a SYNTHETIC
interaction file so music gets the same kind of same-domain collaborative
signal the other two domains already have.

These are clearly synthetic users, not measured human behavior — a data
generation decision, not a substitute for real listening data. Generated via
persona-based sampling over Spotify's own audio features (acousticness,
danceability, energy, instrumentalness, speechiness, valence, tempo), so
each persona's "taste" is grounded in something real about each track:

  - Most users are assigned one of several taste personas (energetic dance-
    pop, moody alternative, chill acoustic, hip-hop, ambient/instrumental,
    classic rock, R&B/soul, happy pop, sad ballads) and sample tracks
    weighted toward that persona's audio-feature profile.
  - A fraction of users are "eclectic" — no dominant persona, sampling
    broadly with only a mild popularity bias — for realistic heterogeneity
    ("all types of behavior and tastes").
  - Each persona draws from a CORE POOL of its best-matching few thousand
    tracks (not the full 130K catalog) — real listening is heavily
    concentrated on a "canon" per taste cluster, not spread evenly. Sampling
    from the full catalog directly produces too little overlap between
    users for any collaborative signal to exist (confirmed empirically: a
    first pass at this gave ALS ~0.0001 Precision@10, i.e. noise). Eclectic
    users draw from a global popular-tracks pool for the same reason.
  - All sampling blends persona/eclectic affinity with track popularity
    (mimicking real long-tail consumption bias) plus noise.
  - Ratings correlate with affinity but aren't deterministic — same
    structure as real rating noise.
  - Interaction counts per user follow a log-normal distribution (a few
    power users, many casual ones), and timestamps are spread across a
    plausible ~3-year window — unlike goodbooks-10k, this lets music
    support genuine temporal walk-forward CV, not just a structural stand-in.

Output: data/raw/music/ratings.csv  (user_id, track_id, rating, timestamp)
"""

import numpy as np
import pandas as pd
from pathlib import Path
from loguru import logger

ROOT      = Path(__file__).resolve().parent.parent
RAW_MUSIC = ROOT / "data" / "raw" / "music"

SEED = 42
N_USERS = 6_000
RATING_MIN, RATING_MAX = 1, 5
ECLECTIC_FRACTION = 0.15
CORE_POOL_SIZE = 350            # per-persona "canon" of best-matching tracks
GLOBAL_POOL_SIZE = 700          # global popular pool eclectic users draw from
TS_START = pd.Timestamp("2022-01-01").timestamp()
TS_END   = pd.Timestamp("2025-01-01").timestamp()

FEATURES = ["acousticness", "danceability", "energy", "instrumentalness", "speechiness", "valence", "tempo"]

# Target audio-feature profile per persona (0-1 scale; tempo normalised by /250 below)
PERSONAS = {
    "energetic_dance_pop":  {"acousticness": 0.10, "danceability": 0.85, "energy": 0.80, "instrumentalness": 0.05, "speechiness": 0.08, "valence": 0.75, "tempo": 0.65},
    "moody_alternative":    {"acousticness": 0.25, "danceability": 0.45, "energy": 0.65, "instrumentalness": 0.10, "speechiness": 0.06, "valence": 0.25, "tempo": 0.50},
    "chill_acoustic_folk":  {"acousticness": 0.85, "danceability": 0.40, "energy": 0.25, "instrumentalness": 0.10, "speechiness": 0.04, "valence": 0.50, "tempo": 0.35},
    "hip_hop_rap":          {"acousticness": 0.15, "danceability": 0.80, "energy": 0.65, "instrumentalness": 0.05, "speechiness": 0.45, "valence": 0.55, "tempo": 0.50},
    "instrumental_ambient": {"acousticness": 0.55, "danceability": 0.30, "energy": 0.20, "instrumentalness": 0.80, "speechiness": 0.03, "valence": 0.45, "tempo": 0.30},
    "classic_rock_anthems": {"acousticness": 0.15, "danceability": 0.50, "energy": 0.85, "instrumentalness": 0.08, "speechiness": 0.05, "valence": 0.65, "tempo": 0.60},
    "late_night_rnb_soul":  {"acousticness": 0.35, "danceability": 0.65, "energy": 0.40, "instrumentalness": 0.05, "speechiness": 0.10, "valence": 0.45, "tempo": 0.40},
    "happy_pop_party":      {"acousticness": 0.08, "danceability": 0.85, "energy": 0.85, "instrumentalness": 0.03, "speechiness": 0.06, "valence": 0.85, "tempo": 0.70},
    "sad_ballads":          {"acousticness": 0.65, "danceability": 0.30, "energy": 0.20, "instrumentalness": 0.05, "speechiness": 0.04, "valence": 0.15, "tempo": 0.30},
}
PERSONA_NAMES = list(PERSONAS.keys())


def load_tracks() -> pd.DataFrame:
    """Mirrors preprocess.py's process_music() filtering exactly, so every
    track_id sampled here is guaranteed to survive into items.csv."""
    tracks = pd.read_csv(RAW_MUSIC / "spotify.csv")
    tracks = tracks.dropna(subset=["track_name"])
    tracks = tracks.drop_duplicates(subset=["track_id"]).reset_index(drop=True)
    return tracks

def normalized_features(tracks: pd.DataFrame) -> pd.DataFrame:
    feats = tracks[FEATURES].copy()
    feats["tempo"] = feats["tempo"].clip(0, 250) / 250.0
    for col in [c for c in FEATURES if c != "tempo"]:
        feats[col] = feats[col].clip(0, 1)
    return feats

def persona_affinity(feats: pd.DataFrame, persona: dict) -> np.ndarray:
    target = np.array([persona[c] for c in FEATURES])
    dist = np.sqrt(((feats[FEATURES].to_numpy() - target) ** 2).sum(axis=1))
    return np.exp(-2.0 * dist)  # smooth falloff: closer in feature space -> higher affinity

def weighted_sample_without_replacement(weights: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """Gumbel-top-k trick: fast, vectorised weighted sampling without replacement."""
    log_w = np.log(np.clip(weights, 1e-12, None))
    gumbel = -np.log(-np.log(rng.random(size=len(weights)) + 1e-12) + 1e-12)
    k = min(k, len(weights))
    return np.argpartition(-(log_w + gumbel), k - 1)[:k]

def build_core_pools(feats: pd.DataFrame, pop_weight: np.ndarray) -> tuple[dict, dict, np.ndarray, np.ndarray]:
    """
    Per persona: the CORE_POOL_SIZE tracks with the highest blended
    affinity+popularity score, with sampling weights renormalised within
    that pool. Same idea for a global popularity-only pool (eclectic users).
    """
    persona_scores = {name: persona_affinity(feats, p) for name, p in PERSONAS.items()}

    core_pool, core_weights = {}, {}
    for name, affinity in persona_scores.items():
        combined = 0.7 * affinity + 0.3 * pop_weight
        idx = np.argpartition(-combined, CORE_POOL_SIZE - 1)[:CORE_POOL_SIZE]
        core_pool[name] = idx
        core_weights[name] = combined[idx] / combined[idx].sum()

    global_idx = np.argpartition(-pop_weight, GLOBAL_POOL_SIZE - 1)[:GLOBAL_POOL_SIZE]
    global_w = pop_weight[global_idx] ** 2  # sharpen: even within "popular," favor the hits
    global_w = global_w / global_w.sum()

    return core_pool, core_weights, global_idx, global_w

def main():
    rng = np.random.default_rng(SEED)
    tracks = load_tracks()
    feats = normalized_features(tracks)
    track_ids = tracks["track_id"].to_numpy()

    pop = tracks["popularity"].fillna(0).to_numpy().astype(float)
    pop_weight = (pop - pop.min()) / (pop.max() - pop.min() + 1e-9)
    persona_scores = {name: persona_affinity(feats, p) for name, p in PERSONAS.items()}
    core_pool, core_weights, global_idx, global_w = build_core_pools(feats, pop_weight)

    rows = []
    for user_id in range(1, N_USERS + 1):
        is_eclectic = rng.random() < ECLECTIC_FRACTION
        n_interactions = int(np.clip(rng.lognormal(mean=3.5, sigma=0.9), 1, 500))

        if is_eclectic:
            pool, pool_weights = global_idx, global_w
            affinity = pop_weight
        else:
            persona = PERSONA_NAMES[rng.integers(len(PERSONA_NAMES))]
            pool, pool_weights = core_pool[persona], core_weights[persona]
            affinity = persona_scores[persona]

        n_interactions = min(n_interactions, len(pool))
        local_chosen = weighted_sample_without_replacement(pool_weights, n_interactions, rng)
        chosen = pool[local_chosen]

        # Rating reflects selection bias: people rate what they chose to listen to more
        # positively on average. Rank affinity WITHIN this user's own chosen tracks (not the
        # raw absolute affinity score, which is usually low even for a "good" match) so the
        # mean lands around ~3.5-3.9, consistent with the real movie (3.5) and book (3.92)
        # rating means elsewhere in this dataset.
        order = np.argsort(affinity[chosen])
        within_user_rank = np.empty(len(chosen))
        denom = max(1, len(chosen) - 1)
        within_user_rank[order] = np.arange(len(chosen)) / denom
        ratings = 2.7 + 2.3 * within_user_rank + rng.normal(0, 0.5, size=len(chosen))
        ratings = np.clip(np.round(ratings), RATING_MIN, RATING_MAX).astype(int)
        timestamps = rng.integers(int(TS_START), int(TS_END), size=len(chosen))
        rows.extend(zip([user_id] * len(chosen), track_ids[chosen], ratings, timestamps))

    out = pd.DataFrame(rows, columns=["user_id", "track_id", "rating", "timestamp"])
    out.to_csv(RAW_MUSIC / "ratings.csv", index=False)

    logger.success(f"Generated {len(out):,} synthetic interactions for {N_USERS:,} users")
    logger.info(f"  Interactions/user: min={out.groupby('user_id').size().min()} "
                f"median={int(out.groupby('user_id').size().median())} max={out.groupby('user_id').size().max()}")
    logger.info(f"  Distinct tracks touched: {out['track_id'].nunique():,}")
    logger.info(f"  Rating distribution:\n{out['rating'].value_counts().sort_index().to_string()}")
    logger.success(f"Saved {RAW_MUSIC / 'ratings.csv'}")

if __name__ == "__main__":
    main()
