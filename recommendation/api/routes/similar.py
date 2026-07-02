import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request

from ..schemas import SimilarItem, SimilarResponse

router = APIRouter()


@router.get("/similar/{item_id}", response_model=SimilarResponse)
def get_similar(item_id: int, request: Request, k: int = Query(10, ge=1, le=50)) -> SimilarResponse:
    store = request.app.state.store
    items = store["items"]
    item_id_to_row = store["item_id_to_row"]

    if item_id not in item_id_to_row:
        raise HTTPException(status_code=404, detail=f"item_id {item_id} not found")

    row = item_id_to_row[item_id]
    query_vec = store["vectors"][row : row + 1]
    distances, indices = store["faiss_index"].search(query_vec, k + 1)  # +1: top hit is the item itself

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == row:
            continue
        r = items.iloc[idx]
        creator = None if pd.isna(r["creator"]) else r["creator"]
        results.append(SimilarItem(item_id=int(r["item_id"]), domain=r["domain"], title=r["title"], creator=creator, score=float(dist)))
        if len(results) >= k:
            break

    source = items.iloc[row]
    return SimilarResponse(item_id=item_id, domain=source["domain"], title=source["title"], results=results)
