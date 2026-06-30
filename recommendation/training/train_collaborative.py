"""
train_collaborative.py

Phase 2 — collaborative filtering via implicit-feedback ALS (Alternating Least
Squares), one model per domain with interactions (movie, book, music).

Per the plan:
  - Minimum interactions per user: 5, per item: 3 (iterative filtering)
  - Temporal walk-forward CV: 3 folds (60/20, 70/20, 80/20 train/test)
  - Offline metrics: Precision@K, Recall@K, NDCG@K, MAP@K (ranking metrics,
    since ALS produces relevance scores, not predicted star ratings)

Our ratings are explicit (1-5 stars, 0.5-5 for movies), not native implicit
signals (play counts, etc). To use ALS as specified, the rating value itself
is used directly as the confidence weight — a common simplification when
adapting explicit data to an implicit-feedback model.

Caveat: goodbooks-10k carries no real timestamps (every book rating has
timestamp=0). True chronological walk-forward CV is therefore only meaningful
for movies and music (both have real, spread-out timestamps); for books the
same fold structure is applied over the existing row order, which is NOT a
real temporal split. This is surfaced via a warning at runtime rather than
silently faked.

Note: music's interactions are SYNTHETIC (persona-based generation over
Spotify's audio features — see pipepline/generate_music_interactions.py),
not measured listening behavior. Its CF model is real and evaluable on its
own terms, but isn't grounded in actual human taste data the way movie/book
ratings are.

Outputs:
  models/als_movie.npz   user_factors, item_factors, user_ids, item_ids
  models/als_book.npz
  models/als_music.npz
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")  # avoid nested threading with implicit's own parallelism

import numpy as np
import pandas as pd
import scipy.sparse as sp
from implicit.als import AlternatingLeastSquares
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import evaluate_recommendations, has_real_timestamps, walk_forward_folds

ROOT   = Path(__file__).resolve().parent.parent
PROC   = ROOT / "data" / "processed"
MODELS = ROOT / "models"
MODELS.mkdir(parents=True, exist_ok=True)

MIN_USER_INTERACTIONS = 5
MIN_ITEM_INTERACTIONS = 3
N_FACTORS  = 64
N_ITERATIONS = 15
REGULARIZATION = 0.01
K = 10


# ── Filtering ─────────────────────────────────────────────────────────────────
def filter_min_interactions(interactions: pd.DataFrame, min_user: int, min_item: int) -> pd.DataFrame:
    """Iteratively drop users/items below the threshold until stable."""
    df = interactions
    while True:
        user_counts = df["user_id"].value_counts()
        item_counts = df["item_id"].value_counts()
        keep_users = user_counts[user_counts >= min_user].index
        keep_items = item_counts[item_counts >= min_item].index
        new_df = df[df["user_id"].isin(keep_users) & df["item_id"].isin(keep_items)]
        if len(new_df) == len(df):
            return new_df
        df = new_df


# ── Encoding + matrix ─────────────────────────────────────────────────────────
def encode(df: pd.DataFrame) -> tuple[sp.csr_matrix, dict, dict, np.ndarray, np.ndarray]:
    user_ids = np.sort(df["user_id"].unique())
    item_ids = np.sort(df["item_id"].unique())
    user_to_idx = {u: i for i, u in enumerate(user_ids)}
    item_to_idx = {it: i for i, it in enumerate(item_ids)}

    rows = df["user_id"].map(user_to_idx).to_numpy()
    cols = df["item_id"].map(item_to_idx).to_numpy()
    vals = df["rating"].to_numpy(dtype=np.float32)  # rating used directly as implicit confidence

    matrix = sp.csr_matrix((vals, (rows, cols)), shape=(len(user_ids), len(item_ids)))
    return matrix, user_to_idx, item_to_idx, user_ids, item_ids


def fit_als(matrix: sp.csr_matrix) -> AlternatingLeastSquares:
    model = AlternatingLeastSquares(
        factors=N_FACTORS,
        regularization=REGULARIZATION,
        iterations=N_ITERATIONS,
        random_state=42,
    )
    model.fit(matrix)
    return model


# ── Fold evaluation ───────────────────────────────────────────────────────────
def evaluate_fold(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    train_matrix, user_to_idx, item_to_idx, user_ids, item_ids = encode(train_df)
    model = fit_als(train_matrix)

    test_users = [u for u in test_df["user_id"].unique() if u in user_to_idx]
    relevant_by_user = (
        test_df[test_df["user_id"].isin(test_users)].groupby("user_id")["item_id"].apply(set).to_dict()
    )
    if not test_users:
        return {"precision@10": 0.0, "recall@10": 0.0, "ndcg@10": 0.0, "map@10": 0.0, "n_users": 0}

    user_indices = np.array([user_to_idx[u] for u in test_users])
    ids_batch, _ = model.recommend(
        user_indices, train_matrix[user_indices], N=K, filter_already_liked_items=True
    )

    recs_by_user = {
        user: [item_ids[col] for col in ids_batch[i] if col >= 0]
        for i, user in enumerate(test_users)
    }
    return evaluate_recommendations(recs_by_user, relevant_by_user, k=K)


# ── Per-domain pipeline ────────────────────────────────────────────────────────
def train_domain(interactions: pd.DataFrame, domain: str) -> None:
    logger.info(f"── {domain.upper()} ──")
    domain_inter = interactions[interactions["domain"] == domain]
    logger.info(f"  Raw: {len(domain_inter):,} interactions, "
                f"{domain_inter['user_id'].nunique():,} users, {domain_inter['item_id'].nunique():,} items")

    filtered = filter_min_interactions(domain_inter, MIN_USER_INTERACTIONS, MIN_ITEM_INTERACTIONS)
    logger.info(f"  Filtered (>={MIN_USER_INTERACTIONS} per user, >={MIN_ITEM_INTERACTIONS} per item): "
                f"{len(filtered):,} interactions, "
                f"{filtered['user_id'].nunique():,} users, {filtered['item_id'].nunique():,} items")

    if not has_real_timestamps(filtered):
        logger.warning(f"  [{domain}] No real timestamps in this dataset — walk-forward folds below are "
                        f"NOT chronological for this domain (structure only, not a true temporal split).")

    fold_metrics = []
    for i, (train_df, test_df) in enumerate(walk_forward_folds(filtered), start=1):
        metrics = evaluate_fold(train_df, test_df)
        fold_metrics.append(metrics)
        logger.success(
            f"  Fold {i} (train={len(train_df):,}, test={len(test_df):,}, n_users={metrics['n_users']:,}): "
            f"Precision@10={metrics['precision@10']:.4f}  Recall@10={metrics['recall@10']:.4f}  "
            f"NDCG@10={metrics['ndcg@10']:.4f}  MAP@10={metrics['map@10']:.4f}"
        )

    avg = {k: float(np.mean([m[k] for m in fold_metrics])) for k in ["precision@10", "recall@10", "ndcg@10", "map@10"]}
    logger.success(
        f"  Average across {len(fold_metrics)} folds: "
        f"Precision@10={avg['precision@10']:.4f}  Recall@10={avg['recall@10']:.4f}  "
        f"NDCG@10={avg['ndcg@10']:.4f}  MAP@10={avg['map@10']:.4f}"
    )

    # Refit on all filtered data for the production model
    full_matrix, user_to_idx, item_to_idx, user_ids, item_ids = encode(filtered)
    final_model = fit_als(full_matrix)

    dest = MODELS / f"als_{domain}.npz"
    np.savez(
        dest,
        user_factors=final_model.user_factors,
        item_factors=final_model.item_factors,
        user_ids=user_ids,
        item_ids=item_ids,
    )
    logger.success(f"  Saved {dest}")


if __name__ == "__main__":
    interactions = pd.read_csv(PROC / "interactions.csv")
    for domain in ["movie", "book", "music"]:
        train_domain(interactions, domain)
