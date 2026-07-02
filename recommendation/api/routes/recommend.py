import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "training"))
from diversify import mmr_rerank, score_candidates_for_user  # noqa: E402
from train_hybrid import recommend_cross_domain  # noqa: E402

from ..schemas import RecommendedItem, RecommendRequest, RecommendResponse

router = APIRouter()

N_CANDIDATES = 100


def _user_home_domain(interactions: pd.DataFrame, user_id: int) -> Optional[str]:
    rows = interactions.loc[interactions["user_id"] == user_id, "domain"]
    return None if rows.empty else rows.mode().iloc[0]


def _item_row(items_by_id: pd.DataFrame, item_id: int) -> RecommendedItem:
    r = items_by_id.loc[item_id]
    creator = None if pd.isna(r["creator"]) else r["creator"]
    return RecommendedItem(item_id=int(item_id), domain=r["domain"], title=r["title"], creator=creator, score=0.0)


def _popularity_fallback(store: dict, domain: str, k: int) -> list[RecommendedItem]:
    """Cold-start fallback: blend interaction-volume popularity with reception quality."""
    items = store["items"]
    popularity, quality = store["popularity"], store["quality"]
    domain_items = items.loc[items["domain"] == domain, ["item_id", "domain", "title", "creator"]].copy()
    domain_items["pop_score"] = domain_items["item_id"].apply(
        lambda iid: 0.5 * popularity.get(iid, 0.0) + 0.5 * quality.get(iid, 0.5)
    )
    top = domain_items.sort_values("pop_score", ascending=False).head(k)
    return [
        RecommendedItem(
            item_id=int(r["item_id"]), domain=r["domain"], title=r["title"],
            creator=None if pd.isna(r["creator"]) else r["creator"], score=float(r["pop_score"]),
        )
        for _, r in top.iterrows()
    ]


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, request: Request) -> RecommendResponse:
    store = request.app.state.store
    interactions = store["interactions"]
    items_by_id = store["items_by_id"]

    home_domain = _user_home_domain(interactions, req.user_id)

    # Cold start: no interaction history anywhere in our data.
    if home_domain is None:
        results = _popularity_fallback(store, req.domain, req.k)
        return RecommendResponse(user_id=req.user_id, domain=req.domain, method="popularity_fallback", results=results)

    # Same-domain: full hybrid pipeline (content + collaborative + LightGBM ranker).
    if home_domain == req.domain:
        try:
            cands = score_candidates_for_user(
                req.user_id, req.domain, N_CANDIDATES,
                store["items"], items_by_id, store["vectors"], store["item_id_to_row"],
                interactions, store["popularity"], store["quality"], store["franchise"], store["year_range"],
                store["ranker"], store["feature_cols"], store["als_data"],
            )
        except ValueError:
            results = _popularity_fallback(store, req.domain, req.k)
            return RecommendResponse(user_id=req.user_id, domain=req.domain, method="popularity_fallback", results=results)

        if req.diversify:
            ranked_ids = mmr_rerank(cands, store["vectors"], store["item_id_to_row"], k=req.k)
        else:
            ranked_ids = cands.sort_values("score", ascending=False)["item_id"].head(req.k).tolist()

        score_map = dict(zip(cands["item_id"], cands["score"]))
        results = []
        for iid in ranked_ids:
            item = _item_row(items_by_id, iid)
            item.score = float(score_map[iid])
            results.append(item)
        return RecommendResponse(user_id=req.user_id, domain=req.domain, method="hybrid", results=results)

    # Cross-domain: content-similarity-only heuristic — NOT validated by the ranker.
    # See training/train_hybrid.py's module docstring for why: there is no genuine
    # ground truth for cross-domain preference in this dataset (disjoint user
    # populations per domain), so this path is a content-similarity demo, not an
    # evaluated capability. Surfaced to the caller via `method` so the web app can
    # label it differently (e.g. "you might also like" vs. a stronger claim).
    try:
        recs_df = recommend_cross_domain(
            req.user_id, req.domain, store["items"], store["vectors"],
            store["user_ids"], store["user_vecs"], k=req.k,
        )
    except ValueError:
        results = _popularity_fallback(store, req.domain, req.k)
        return RecommendResponse(user_id=req.user_id, domain=req.domain, method="popularity_fallback", results=results)

    results = [
        RecommendedItem(
            item_id=int(r["item_id"]), domain=req.domain, title=r["title"],
            creator=None if pd.isna(r["creator"]) else r["creator"], score=float(r["score"]),
        )
        for _, r in recs_df.iterrows()
    ]
    return RecommendResponse(user_id=req.user_id, domain=req.domain, method="cross_domain_content", results=results)
