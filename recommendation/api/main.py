"""
FastAPI entry point for the Trackify recommendation microservice.

All trained artifacts (embeddings, FAISS index, ALS factors, the LightGBM
hybrid ranker, and precomputed popularity/quality/franchise maps) are loaded
ONCE at startup into app.state.store and reused across requests — none of the
route handlers touch disk per-request.

Run with:  uvicorn api.main:app --reload   (from the recommendation/ directory)
"""

import pickle
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import faiss
import numpy as np
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "training"))

from diversify import load_als  # noqa: E402
from train_hybrid import load_globals, year_bounds  # noqa: E402

from .routes import health, recommend, similar

EMB = ROOT / "embeddings"
MODELS = ROOT / "models"


@asynccontextmanager
async def lifespan(app: FastAPI):
    items, vectors, item_id_to_row, interactions, popularity, quality, franchise = load_globals()
    with open(MODELS / "hybrid_ranker.pkl", "rb") as f:
        saved = pickle.load(f)

    app.state.store = {
        "items": items,
        "items_by_id": items.set_index("item_id"),
        "vectors": vectors,
        "item_id_to_row": item_id_to_row,
        "interactions": interactions,
        "popularity": popularity,
        "quality": quality,
        "franchise": franchise,
        "year_range": year_bounds(items),
        "ranker": saved["model"],
        "feature_cols": saved["feature_cols"],
        "als_data": {d: load_als(d) for d in ["movie", "book", "music"]},
        "faiss_index": faiss.read_index(str(EMB / "item_index.faiss")),
        "user_ids": np.load(MODELS / "user_vectors_ids.npy"),
        "user_vecs": np.load(MODELS / "user_vectors.npy"),
    }
    yield
    app.state.store.clear()


app = FastAPI(title="Trackify Recommendation Service", lifespan=lifespan)
app.include_router(health.router)
app.include_router(similar.router)
app.include_router(recommend.router)
