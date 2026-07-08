import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class MediaItem(Base):
    __tablename__ = "media_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    domain: Mapped[str] = mapped_column(String, nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String, nullable=False)
    rec_item_id: Mapped[int | None] = mapped_column(Integer, unique=True, default=None)
    title: Mapped[str] = mapped_column(String, nullable=False)
    creator: Mapped[str | None] = mapped_column(String, default=None)
    year: Mapped[int | None] = mapped_column(Integer, default=None)
    genres: Mapped[str | None] = mapped_column(Text, default=None)
    tags: Mapped[str | None] = mapped_column(Text, default=None)
    overview: Mapped[str | None] = mapped_column(Text, default=None)
    cover_url: Mapped[str | None] = mapped_column(String, default=None)
    external_url: Mapped[str | None] = mapped_column(String, default=None)
    popularity: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (UniqueConstraint("domain", "external_id"),)


class UserLibrary(Base):
    __tablename__ = "user_library"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_items.id"), nullable=False)
    item: Mapped[MediaItem] = relationship(lazy="joined")
    status: Mapped[str] = mapped_column(String, nullable=False, default="want")
    progress: Mapped[int | None] = mapped_column(Integer, default=None)
    progress_total: Mapped[int | None] = mapped_column(Integer, default=None)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (UniqueConstraint("user_id", "item_id"),)
