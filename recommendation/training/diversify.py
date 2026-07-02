"""
diversify.py

Phase 4 — diversity, exploration, and post-ranking adjustments applied on top
of the Phase 3 hybrid ranker's output.

Implemented (all computable from data we actually have):
  MMR (Maximal Marginal Relevance)   greedy relevance-vs-redundancy tradeoff
  Greedy DPP MAP inference           full-list quality+diversity (Chen et al. 2018)
  Slot-based rules                   position 1-2 relevance, 3 different genre,
                                      4 collaborative signal, 5 serendipity
  epsilon-greedy exploration         swap a fraction of slots for random unseen items
  UCB-style exploration bonus        uncertainty bonus for under-exposed items
  ILD / catalog coverage             diversity metrics to compare the above

Explicitly NOT implemented — blocked by missing data, not a judgment call:
  IPS (inverse propensity scoring)   would need real exposure logs (what was
                                      shown vs. just what was rated); we only
                                      have ratings, so "propensity" below is
                                      approximated from item_popularity and
                                      should be read as a demo, not a real
                                      debiasing correction.
  Causal inference                  needs online A/B-style logs distinguishing
                                      organic preference from recommendation-
                                      induced clicks; this is an offline
                                      historical-ratings dataset, no such signal
                                      exists.
  Social signals (trust graph,       no friend/social graph data exists
  tribe detection, taste leaders)    anywhere in this dataset.
"""

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_hybrid import build_features, user_history_profiles, load_globals, year_bounds

ROOT   = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"


# ── Serving-time candidate scoring (reuses Phase 3's feature pipeline) ────────
def load_als(domain: str):
    data = np.load(MODELS / f"als_{domain}.npz")
    user_to_idx = {u: i for i, u in enumerate(data["user_ids"])}
    item_to_idx = {it: i for i, it in enumerate(data["item_ids"])}
    return data["user_factors"], data["item_factors"], user_to_idx, item_to_idx


def score_candidates_for_user(
    user_id: int, domain: str, n_candidates: int,
    items, items_by_id, vectors, item_id_to_row, interactions, popularity, quality, franchise, year_range,
    ranker, feature_cols, als_data: dict,
) -> pd.DataFrame:
    user_factors, item_factors, als_user_to_idx, als_item_to_idx = als_data[domain]

    domain_mask = (items["domain"] == domain).to_numpy()
    domain_vectors = vectors[domain_mask]
    domain_item_ids = items.loc[domain_mask, "item_id"].to_numpy()

    history = interactions[(interactions["user_id"] == user_id) & (interactions["domain"] == domain)]
    seen_items = set(history["item_id"])
    seen_cols = [i for i, iid in enumerate(domain_item_ids) if iid in seen_items]
    if not seen_cols:
        raise ValueError(f"User {user_id} has no {domain} history to build a profile from")

    profile = domain_vectors[seen_cols].mean(axis=0)
    norm = np.linalg.norm(profile)
    profile = profile / norm if norm > 0 else profile

    scores = domain_vectors @ profile
    scores[seen_cols] = -np.inf
    top = np.argpartition(-scores, min(n_candidates, len(scores) - 1))[:n_candidates]
    candidate_ids = domain_item_ids[top].tolist()

    def als_score_fn(item_id):
        if user_id not in als_user_to_idx or item_id not in als_item_to_idx:
            return 0.0
        return float(user_factors[als_user_to_idx[user_id]] @ item_factors[als_item_to_idx[item_id]])

    history_profile = user_history_profiles(history, items).get(user_id, {})
    feats = build_features(
        user_id, domain, candidate_ids, profile, als_score_fn,
        items_by_id, item_id_to_row, vectors, popularity, quality, franchise,
        history_profile, year_range, user_domain_fracs={domain: 1.0},
    )
    feats["score"] = ranker.predict(feats[feature_cols])
    return feats


# ── MMR ────────────────────────────────────────────────────────────────────────
def mmr_rerank(candidates: pd.DataFrame, vectors, item_id_to_row: dict, k: int = 10, lambda_param: float = 0.7) -> list:
    pool = candidates[["item_id", "score"]].copy()
    rel = pool["score"].to_numpy()
    pool["norm_score"] = (rel - rel.min()) / (rel.max() - rel.min() + 1e-9)

    selected_ids, selected_vecs = [], []
    pool_ids = pool["item_id"].tolist()
    pool_scores = dict(zip(pool["item_id"], pool["norm_score"]))

    while len(selected_ids) < k and pool_ids:
        if not selected_vecs:
            mmr = {iid: pool_scores[iid] for iid in pool_ids}
        else:
            sel_matrix = np.array(selected_vecs)
            mmr = {}
            for iid in pool_ids:
                v = vectors[item_id_to_row[iid]]
                max_sim = float((sel_matrix @ v).max())
                mmr[iid] = lambda_param * pool_scores[iid] - (1 - lambda_param) * max_sim
        best = max(mmr, key=mmr.get)
        selected_ids.append(best)
        selected_vecs.append(vectors[item_id_to_row[best]])
        pool_ids.remove(best)
    return selected_ids


# ── Greedy DPP MAP inference (Chen et al. 2018) ───────────────────────────────
def dpp_rerank(candidates: pd.DataFrame, vectors, item_id_to_row: dict, k: int = 10, theta: float = 3.0) -> list:
    item_ids = candidates["item_id"].to_numpy()
    rel = candidates["score"].to_numpy()
    rel = (rel - rel.min()) / (rel.max() - rel.min() + 1e-9)
    vecs = np.array([vectors[item_id_to_row[i]] for i in item_ids])

    sim = vecs @ vecs.T  # cosine similarity (vectors are L2-normalised)
    q = np.exp(theta * rel)
    L = np.outer(q, q) * sim

    n = len(item_ids)
    k = min(k, n)
    selected = []
    di2 = np.diag(L).copy()
    cis = np.zeros((k, n))
    for t in range(k):
        j = int(np.argmax(di2))
        if di2[j] < 1e-10:
            break
        selected.append(j)
        eis = (L[j, :] - cis[:t, j].T @ cis[:t, :]) / np.sqrt(di2[j])
        cis[t, :] = eis
        di2 -= eis ** 2
        di2[j] = -np.inf
    return item_ids[selected].tolist()


# ── Slot-based rules ───────────────────────────────────────────────────────────
def slot_based_rerank(candidates: pd.DataFrame, items_by_id: pd.DataFrame, k: int = 5) -> list:
    pool = candidates.sort_values("score", ascending=False).reset_index(drop=True)

    def genres_of(item_id) -> set:
        raw = items_by_id.loc[item_id, "genres"]
        return set() if pd.isna(raw) else {g.strip() for g in str(raw).split(",") if g.strip()}

    slots = [pool.iloc[0]["item_id"], pool.iloc[1]["item_id"]]
    used_genres = genres_of(slots[0]) | genres_of(slots[1])
    remaining = pool[~pool["item_id"].isin(slots)]
    diff_genre = remaining[remaining["item_id"].apply(lambda i: not (genres_of(i) & used_genres))]
    slot3 = diff_genre.iloc[0]["item_id"] if len(diff_genre) else remaining.iloc[0]["item_id"]
    slots.append(slot3)
    remaining = remaining[remaining["item_id"] != slot3]
    slot4 = remaining.sort_values("collaborative_score", ascending=False).iloc[0]["item_id"]
    slots.append(slot4)
    remaining = remaining[remaining["item_id"] != slot4]

    serendipity_pool = remaining[remaining["score"] > remaining["score"].quantile(0.3)]
    serendipity_pool = serendipity_pool if len(serendipity_pool) else remaining
    slot5 = serendipity_pool.sort_values("content_similarity_score").iloc[0]["item_id"]
    slots.append(slot5)
    return slots[:k]

# ── Exploration ────────────────────────────────────────────────────────────────
def epsilon_greedy_select(ranked_ids: list, candidate_pool: list, k: int = 10, epsilon: float = 0.1, rng=None) -> list:
    rng = rng or np.random.default_rng()
    n_explore = max(1, round(k * epsilon))
    n_exploit = k - n_explore
    exploit = ranked_ids[:n_exploit]
    unseen_pool = [i for i in candidate_pool if i not in exploit]
    n_explore = min(n_explore, len(unseen_pool))
    explore = rng.choice(unseen_pool, size=n_explore, replace=False).tolist() if n_explore else []
    return exploit + explore

def ucb_bonus(candidates: pd.DataFrame, exposure_count: dict, total_exposures: int, c: float = 0.3) -> pd.Series:
    """
    Uncertainty bonus for under-exposed items, classic UCB1 form.
    exposure_count is approximated from historical interaction counts (popularity)
    since we have no real impression/exposure logs — items we have few ratings
    for are treated as "under-explored," which is a reasonable proxy but not
    the same as true exposure.
    """
    n_i = candidates["item_id"].map(exposure_count).fillna(0).to_numpy() + 1
    return c * np.sqrt(np.log(total_exposures + 1) / n_i)

def ips_weight(candidates: pd.DataFrame, popularity: dict, epsilon: float = 0.01) -> pd.Series:
    """
    Approximate inverse propensity weight using item_popularity as a stand-in
    for true exposure propensity. NOT a real IPS correction (see module
    docstring) — useful only to demonstrate how upweighting niche items shifts
    a ranked list, not as a validated debiasing method.
    """
    propensity = candidates["item_id"].map(popularity).fillna(epsilon).clip(lower=epsilon)
    return 1.0 / propensity

# ── Diversity metrics ──────────────────────────────────────────────────────────
def intra_list_diversity(item_ids: list, vectors, item_id_to_row: dict) -> float:
    if len(item_ids) < 2:
        return 0.0
    vecs = np.array([vectors[item_id_to_row[i]] for i in item_ids])
    sims = vecs @ vecs.T
    iu = np.triu_indices(len(item_ids), k=1)
    return float(1 - sims[iu].mean())

def catalog_coverage(recommended_ids: set, catalog_size: int) -> float:
    return len(recommended_ids) / catalog_size

# ── Demo ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    items, vectors, item_id_to_row, interactions, popularity, quality, franchise = load_globals()
    year_range = year_bounds(items)
    items_by_id = items.set_index("item_id")

    with open(MODELS / "hybrid_ranker.pkl", "rb") as f:
        saved = pickle.load(f)
    ranker, feature_cols = saved["model"], saved["feature_cols"]

    domain = "movie"
    als_data = {d: load_als(d) for d in ["movie", "book", "music"]}
    sample_users = (
        interactions.loc[interactions["domain"] == domain, "user_id"]
        .drop_duplicates().sample(30, random_state=11).tolist()
    )

    print(f"\n── Phase 4: diversity & exploration demo ({domain}, K=10) ──")
    plain_coverage, mmr_coverage, dpp_coverage = set(), set(), set()
    plain_ild, mmr_ild, dpp_ild = [], [], []

    for i, user_id in enumerate(sample_users):
        try:
            cands = score_candidates_for_user(
                user_id, domain, 100, items, items_by_id, vectors, item_id_to_row, interactions,
                popularity, quality, franchise, year_range, ranker, feature_cols, als_data,
            )
        except ValueError:
            continue

        plain = cands.sort_values("score", ascending=False)["item_id"].head(10).tolist()
        mmr = mmr_rerank(cands, vectors, item_id_to_row, k=10, lambda_param=0.7)
        dpp = dpp_rerank(cands, vectors, item_id_to_row, k=10)
        plain_coverage.update(plain); mmr_coverage.update(mmr); dpp_coverage.update(dpp)
        plain_ild.append(intra_list_diversity(plain, vectors, item_id_to_row))
        mmr_ild.append(intra_list_diversity(mmr, vectors, item_id_to_row))
        dpp_ild.append(intra_list_diversity(dpp, vectors, item_id_to_row))

        if i == 0:
            slots = slot_based_rerank(cands, items_by_id, k=5)
            exploit_then_explore = epsilon_greedy_select(plain, cands["item_id"].tolist(), k=10, epsilon=0.1,
                                                           rng=np.random.default_rng(0))
            print(f"\n  Sample user {user_id}:")
            print(f"    Plain top-10 titles:  {items_by_id.loc[plain[:5], 'title'].tolist()} ...")
            print(f"    MMR top-10 titles:    {items_by_id.loc[mmr[:5], 'title'].tolist()} ...")
            print(f"    DPP top-10 titles:    {items_by_id.loc[dpp[:5], 'title'].tolist()} ...")
            print(f"    Slot-based top-5:     {items_by_id.loc[slots, 'title'].tolist()}")
            print(f"    ε-greedy (last item is explored): {items_by_id.loc[[exploit_then_explore[-1]], 'title'].tolist()}")

    catalog_size = int((items["domain"] == domain).sum())
    print(f"\n  Across {len(plain_ild)} sample users (out of {len(sample_users)} requested):")
    print(f"    {'Method':<8} {'Avg ILD':>10} {'Coverage':>12}")
    for name, ild_list, cov in [
        ("Plain", plain_ild, plain_coverage),
        ("MMR", mmr_ild, mmr_coverage),
        ("DPP", dpp_ild, dpp_coverage),
    ]:
        print(f"    {name:<8} {np.mean(ild_list):>10.4f} {catalog_coverage(cov, catalog_size):>11.2%}")