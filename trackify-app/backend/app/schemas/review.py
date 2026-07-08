import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    item_id: uuid.UUID
    rating: float | None = Field(default=None, ge=0.5, le=5.0)
    body: str | None = None
    contains_spoiler: bool = False


class ReviewUpdate(BaseModel):
    rating: float | None = Field(default=None, ge=0.5, le=5.0)
    body: str | None = None
    contains_spoiler: bool | None = None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    item_id: uuid.UUID
    rating: float | None
    body: str | None
    contains_spoiler: bool
    created_at: datetime
    updated_at: datetime | None
