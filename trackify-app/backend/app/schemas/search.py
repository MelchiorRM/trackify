from typing import Literal

from pydantic import BaseModel

Domain = Literal["movie", "book", "music"]


class SearchResult(BaseModel):
    external_id: str
    domain: Domain
    title: str
    creator: str | None = None
    year: int | None = None
    genres: list[str] = []
    overview: str | None = None
    cover_url: str | None = None
    external_url: str | None = None
    popularity: float | None = None


class SearchResponse(BaseModel):
    query: str
    domain: Domain | None = None
    results: list[SearchResult]
