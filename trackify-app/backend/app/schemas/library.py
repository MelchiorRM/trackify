import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .media_item import MediaItemRead

Status = Literal["want", "in_progress", "completed", "dropped"]


class LibraryCreate(BaseModel):
    domain: Literal["movie", "book", "music"]
    external_id: str


class LibraryUpdate(BaseModel):
    status: Status | None = None
    progress: int | None = Field(default=None, ge=0)
    progress_total: int | None = Field(default=None, ge=0)


class LibraryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item: MediaItemRead
    status: Status
    progress: int | None
    progress_total: int | None
    added_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    updated_at: datetime | None
