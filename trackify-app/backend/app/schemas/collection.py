import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .media_item import MediaItemRead


class CollectionCreate(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = True


class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None


class CollectionItemCreate(BaseModel):
    domain: str
    external_id: str
    note: str | None = None


class CollectionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item: MediaItemRead
    position: int
    note: str | None
    added_at: datetime


class CollectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    is_public: bool
    created_at: datetime
    items: list[CollectionItemRead] = []
