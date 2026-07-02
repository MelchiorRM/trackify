"""Pydantic request/response models for the recommendation service."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    items_loaded: int
    domains: list[str]


class SimilarItem(BaseModel):
    item_id: int
    domain: str
    title: str
    creator: Optional[str] = None
    score: float


class SimilarResponse(BaseModel):
    item_id: int
    domain: str
    title: str
    results: list[SimilarItem]


class RecommendRequest(BaseModel):
    user_id: int
    domain: Literal["movie", "book", "music"]
    k: int = Field(default=10, ge=1, le=50)
    diversify: bool = True


class RecommendedItem(BaseModel):
    item_id: int
    domain: str
    title: str
    creator: Optional[str] = None
    score: float


class RecommendResponse(BaseModel):
    user_id: int
    domain: str
    # Tells the caller how the list was produced, since these carry very different
    # confidence levels — see training/train_hybrid.py's module docstring for why
    # cross_domain_content is an unvalidated heuristic, not an evaluated capability.
    method: Literal["hybrid", "cross_domain_content", "popularity_fallback"]
    results: list[RecommendedItem]
