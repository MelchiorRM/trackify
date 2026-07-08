import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class MediaItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    domain: str
    external_id: str
    title: str
    creator: str | None
    year: int | None
    genres: list[str]
    overview: str | None
    cover_url: str | None
    external_url: str | None
    popularity: float | None
    created_at: datetime

    @field_validator("genres", mode="before")
    @classmethod
    def split_genres(cls, value):
        if isinstance(value, str):
            return [g for g in value.split(",") if g]
        return value or []
