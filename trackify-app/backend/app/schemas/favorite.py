import uuid

from pydantic import BaseModel, ConfigDict, Field

from .media_item import MediaItemRead


class FavoritesUpdate(BaseModel):
    item_ids: list[uuid.UUID] = Field(max_length=4)


class FavoriteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item: MediaItemRead
    position: int
