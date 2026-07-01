"""
evaluate.py

Shared offline ranking metrics and split helpers used by both:
  - Phase 1 content-based evaluation (this script's __main__)
  - Phase 2 collaborative evaluation (imported by train_collaborative.py)

Metrics operate on a ranked prediction list vs. a relevant-item set, per the
plan's chosen offline metrics: Precision@K, Recall@K, NDCG@K, MAP@K.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"


# ── Ranking metrics ──────────────────────────────────────────────────────────
def precision_at_k(predicted: list, relevant: set, k: int) -> float:
    if k == 0:
        return 0.0
    top_k = predicted[:k]
    return sum(1 for item in top_k if item in relevant) / k


def recall_at_k(predicted: list, relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    top_k = predicted[:k]
    return sum(1 for item in top_k if item in relevant) / len(relevant)


def ndcg_at_k(predicted: list, relevant: set, k: int) -> float:
    top_k = predicted[:k]
    dcg = sum(1.0 / np.log2(i + 2) for i, item in enumerate(top_k) if item in relevant)
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0

def average_precision_at_k(predicted: list, relevant: set, k: int) -> float:
    """AP@k for one user; mean across users gives MAP@k."""
    if not relevant:
        return 0.0
    hits, score = 0, 0.0
    for i, item in enumerate(predicted[:k]):
        if item in relevant:
            hits += 1
            score += hits / (i + 1)
    return score / min(len(relevant), k)

def evaluate_recommendations(recs_by_user: dict, relevant_by_user: dict, k: int = 10) -> dict:
    """
    recs_by_user:     {user_id: [ranked item_id, ...]}
    relevant_by_user: {user_id: {held-out relevant item_id, ...}}
    Returns mean Precision/Recall/NDCG/MAP@k across users that have >=1 relevant item.
    """
    precisions, recalls, ndcgs, aps = [], [], [], []
    for user, relevant in relevant_by_user.items():
        if not relevant:
            continue
        predicted = recs_by_user.get(user, [])
        precisions.append(precision_at_k(predicted, relevant, k))
        recalls.append(recall_at_k(predicted, relevant, k))
        ndcgs.append(ndcg_at_k(predicted, relevant, k))
        aps.append(average_precision_at_k(predicted, relevant, k))
    return {
        f"precision@{k}": float(np.mean(precisions)) if precisions else 0.0,
        f"recall@{k}":    float(np.mean(recalls)) if recalls else 0.0,
        f"ndcg@{k}":      float(np.mean(ndcgs)) if ndcgs else 0.0,
        f"map@{k}":       float(np.mean(aps)) if aps else 0.0,
        "n_users":        len(precisions),
    }

# ── Split helpers ─────────────────────────────────────────────────────────────
def temporal_holdout_per_user(interactions: pd.DataFrame, test_frac: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Per-user temporal holdout: sort each user's interactions by timestamp,
    take the last test_frac as test. Users with <2 interactions go entirely to train.
    Meaningful only when timestamps are real (non-constant) for that domain.
    """
    train_parts, test_parts = [], []
    for _, group in interactions.groupby("user_id"):
        group = group.sort_values("timestamp")
        n_test = int(len(group) * test_frac) if len(group) > 1 else 0
        if n_test == 0:
            train_parts.append(group)
        else:
            train_parts.append(group.iloc[:-n_test])
            test_parts.append(group.iloc[-n_test:])
    train = pd.concat(train_parts, ignore_index=True) if train_parts else interactions.iloc[0:0]
    test = pd.concat(test_parts, ignore_index=True) if test_parts else interactions.iloc[0:0]
    return train, test


def walk_forward_folds(interactions: pd.DataFrame, fold_fracs=((0.6, 0.2), (0.7, 0.2), (0.8, 0.2))) -> list:
    """
    Global walk-forward folds over time-sorted interactions:
      Fold 1: [first 60%] train -> [next 20%] test
      Fold 2: [first 70%] train -> [next 20%] test
      Fold 3: [first 80%] train -> [last 20%] test
    Requires a domain with real, non-constant timestamps to be meaningful.
    """
    sorted_df = interactions.sort_values("timestamp").reset_index(drop=True)
    n = len(sorted_df)
    folds = []
    for train_frac, test_frac in fold_fracs:
        train_end = int(n * train_frac)
        test_end = int(n * (train_frac + test_frac))
        folds.append((sorted_df.iloc[:train_end].copy(), sorted_df.iloc[train_end:test_end].copy()))
    return folds


def has_real_timestamps(interactions: pd.DataFrame) -> bool:
    return interactions["timestamp"].nunique() > 1


# ── Phase 1: content-based evaluation (FAISS-equivalent dot product) ─────────
def evaluate_content_based(domain: str, k: int = 10, test_frac: float = 0.2, max_users: int = 2000) -> dict:
    interactions = pd.read_csv(PROC / "interactions.csv")
    vectors = np.load(ROOT / "embeddings" / "item_vectors.npy")

    # item_vectors.npy rows align 1:1 with items.csv rows (same order)
    items = pd.read_csv(PROC / "items.csv", usecols=["item_id", "domain"])
    domain_mask = (items["domain"] == domain).to_numpy()
    domain_vectors = vectors[domain_mask]
    domain_item_ids = items.loc[domain_mask, "item_id"].to_numpy()
    id_to_col = {iid: i for i, iid in enumerate(domain_item_ids)}

    domain_inter = interactions[interactions["domain"] == domain]
    if not has_real_timestamps(domain_inter):
        logger.warning(f"  [{domain}] timestamps are constant (no real temporal data) — "
                        f"holdout split will not be chronological for this domain.")

    train_df, test_df = temporal_holdout_per_user(domain_inter, test_frac=test_frac)

    test_users = test_df["user_id"].unique()
    if len(test_users) > max_users:
        test_users = np.random.default_rng(42).choice(test_users, size=max_users, replace=False)

    train_by_user = train_df.groupby("user_id")["item_id"].apply(set).to_dict()
    relevant_by_user = test_df[test_df["user_id"].isin(test_users)].groupby("user_id")["item_id"].apply(set).to_dict()

    recs_by_user = {}
    for user in test_users:
        train_items = [id_to_col[i] for i in train_by_user.get(user, set()) if i in id_to_col]
        if not train_items:
            continue
        profile = domain_vectors[train_items].mean(axis=0)
        norm = np.linalg.norm(profile)
        if norm > 0:
            profile = profile / norm
        scores = domain_vectors @ profile
        scores[train_items] = -np.inf  # exclude already-seen items
        top_cols = np.argpartition(-scores, k)[:k]
        top_cols = top_cols[np.argsort(-scores[top_cols])]
        recs_by_user[user] = [domain_item_ids[c] for c in top_cols]

    metrics = evaluate_recommendations(recs_by_user, relevant_by_user, k=k)
    metrics["domain"] = domain
    metrics["method"] = "content-based (TF-IDF+SVD embeddings)"
    return metrics

if __name__ == "__main__":
    print("\n── Phase 1: content-based evaluation (temporal per-user holdout) ──")
    for domain in ["movie", "book", "music"]:
        metrics = evaluate_content_based(domain, k=10)
        logger.success(
            f"  [{domain.upper()}] n_users={metrics['n_users']:,}  "
            f"Precision@10={metrics['precision@10']:.4f}  "
            f"Recall@10={metrics['recall@10']:.4f}  "
            f"NDCG@10={metrics['ndcg@10']:.4f}  "
            f"MAP@10={metrics['map@10']:.4f}"
        )