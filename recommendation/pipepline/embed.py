"""
embed.py

Encodes every item's text field using TF-IDF + Truncated SVD (LSA).
Fully local — no model downloads required.
When sentence-transformers becomes available (production / your machine),
swap embed_items() for the SentenceTransformer version at the bottom.

Produces:
  embeddings/item_vectors.npy   — (N, 128) float32 array (L2-normalised)
  embeddings/item_index.faiss   — FAISS flat inner product index
  embeddings/item_id_map.csv    — faiss row → item metadata
  embeddings/tfidf_vectorizer.pkl + svd_model.pkl  — saved pipeline
"""

import pickle
import numpy as np
import pandas as pd
import faiss
from pathlib import Path
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
EMB  = ROOT / "embeddings"
EMB.mkdir(parents=True, exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
N_COMPONENTS = 128      # embedding dimension
MAX_FEATURES = 20_000   # TF-IDF vocabulary size
NGRAM_RANGE  = (1, 2)   # unigrams + bigrams


# ── Load ──────────────────────────────────────────────────────────────────────
def load_items() -> pd.DataFrame:
    items = pd.read_csv(PROC / "items.csv")
    items["text"] = items["text"].fillna(items["title"]).fillna("").str.strip()
    items = items[items["text"] != ""].reset_index(drop=True)
    logger.info(f"Loaded {len(items):,} items")
    return items

# ── Embed ─────────────────────────────────────────────────────────────────────
def embed_items(items: pd.DataFrame) -> np.ndarray:
    texts = items["text"].tolist()
    logger.info(f"Fitting TF-IDF (max_features={MAX_FEATURES}, ngrams={NGRAM_RANGE})...")

    tfidf = TfidfVectorizer(
        max_features=MAX_FEATURES,
        ngram_range=NGRAM_RANGE,
        sublinear_tf=True,          # log(1+tf) — reduces impact of very frequent terms
        min_df=2,                   # ignore terms appearing in < 2 docs
        strip_accents="unicode",
        analyzer="word",
    )
    X_sparse = tfidf.fit_transform(texts)
    logger.info(f"  TF-IDF matrix: {X_sparse.shape}")
    logger.info(f"Fitting SVD (n_components={N_COMPONENTS})...")
    svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=42, n_iter=10)
    X_dense = svd.fit_transform(X_sparse)
    explained = svd.explained_variance_ratio_.sum()
    logger.info(f"  Explained variance: {explained:.3f}")

    # L2-normalise → cosine similarity = dot product
    X_norm = normalize(X_dense, norm="l2").astype(np.float32)
    logger.success(f"Embeddings ready: {X_norm.shape}")

    # Save sklearn objects for inference
    with open(EMB / "tfidf_vectorizer.pkl", "wb") as f:
        pickle.dump(tfidf, f)
    with open(EMB / "svd_model.pkl", "wb") as f:
        pickle.dump(svd, f)

    return X_norm

# ── FAISS ─────────────────────────────────────────────────────────────────────
def build_faiss_index(vectors: np.ndarray) -> faiss.IndexFlatIP:
    dim   = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)   # exact cosine (vectors are normalised)
    index.add(vectors)
    logger.success(f"FAISS index: {index.ntotal:,} vectors, dim={dim}")
    return index

# ── Save ──────────────────────────────────────────────────────────────────────
def save(items: pd.DataFrame, vectors: np.ndarray, index: faiss.IndexFlatIP) -> None:
    np.save(EMB / "item_vectors.npy", vectors)
    faiss.write_index(index, str(EMB / "item_index.faiss"))

    id_map = items[["item_id", "domain", "title", "creator", "genres", "tags"]].copy()
    id_map["faiss_row"] = id_map.index
    id_map.to_csv(EMB / "item_id_map.csv", index=False)
    logger.success(f"All files saved to {EMB}")

# ── Sanity check ──────────────────────────────────────────────────────────────
def sanity_check(index: faiss.IndexFlatIP, vectors: np.ndarray) -> None:
    id_map = pd.read_csv(EMB / "item_id_map.csv")
    test_queries = [
        "Dark Knight",
        "Dune",
        "Kind of Blue",
        "A Love Supreme",
        "Catcher in the Rye",
        "Hans Zimmer",
        "Pink Floyd",
    ]

    print("\n── Sanity check: cross-domain nearest neighbours ────────────────")
    for query in test_queries:
        matches = id_map[id_map["title"].str.contains(query, case=False, na=False)]
        if matches.empty:
            matches = id_map[id_map["creator"].str.contains(query, case=False, na=False)]
        if matches.empty:
            continue

        row    = int(matches.iloc[0]["faiss_row"])
        q_vec  = vectors[row].reshape(1, -1)
        D, I   = index.search(q_vec, 9)   # top-9 (index 0 = self)

        source = id_map.iloc[row]
        print(f"\n  [{source['domain'].upper()}] {source['title']}")
        for dist, idx in zip(D[0][1:], I[0][1:]):
            nb = id_map.iloc[int(idx)]
            print(f"    [{nb['domain'].upper():5}] {nb['title'][:55]:<55} sim={dist:.3f}")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    items   = load_items()
    vectors = embed_items(items)
    index   = build_faiss_index(vectors)
    save(items, vectors, index)
    sanity_check(index, vectors)
    print("\n── Embedding stats ──────────────────────────────────────────────")
    print(f"  Shape     : {vectors.shape}")
    print(f"  Dtype     : {vectors.dtype}")
    print(f"  Norm mean : {np.linalg.norm(vectors, axis=1).mean():.4f}  (should be ~1.0)")
    print(f"  Files     :")
    for f in sorted(EMB.iterdir()):
        size = f.stat().st_size / 1024
        print(f"    {f.name:<35} {size:8.1f} KB")