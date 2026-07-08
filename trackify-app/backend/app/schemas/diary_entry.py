import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DiaryEntryCreate(BaseModel):
    logged_at: date
    rewatch: bool = False
    rating: float | None = Field(default=None, ge=0.5, le=5.0)
    note: str | None = None


class DiaryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: uuid.UUID
    library_id: uuid.UUID
    logged_at: date
    rewatch: bool
    rating: float | None
    note: str | None
    created_at: datetime
