from collections import Counter
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.diary_entry import DiaryEntry
from ..models.media_item import MediaItem, UserLibrary
from ..models.review import Review
from ..models.user import User
from ..schemas.stats import GenreCount, MonthlyBucket, StatsRead

DOMAINS = ("movie", "book", "music")


def _longest_streak(logged_dates: list[date]) -> int:
    if not logged_dates:
        return 0
    longest = current = 1
    for previous, current_date in zip(logged_dates, logged_dates[1:]):
        if (current_date - previous).days == 1:
            current += 1
        else:
            current = 1
        longest = max(longest, current)
    return longest


async def _counts_by_domain(db: AsyncSession, user: User, *, completed_only: bool) -> dict[str, int]:
    query = (
        select(MediaItem.domain, func.count(UserLibrary.id))
        .select_from(UserLibrary)
        .join(MediaItem, UserLibrary.item_id == MediaItem.id)
        .where(UserLibrary.user_id == user.id)
        .group_by(MediaItem.domain)
    )
    if completed_only:
        query = query.where(UserLibrary.status == "completed")
    result = await db.execute(query)
    counts = dict(result.all())
    return {domain: counts.get(domain, 0) for domain in DOMAINS}


async def _ratings_distribution(db: AsyncSession, user: User) -> dict[int, int]:
    result = await db.execute(
        select(Review.rating).where(Review.user_id == user.id, Review.rating.isnot(None))
    )
    distribution = {star: 0 for star in range(1, 6)}
    for rating in result.scalars().all():
        star = min(5, max(1, round(rating)))
        distribution[star] += 1
    return distribution


async def _top_genres(db: AsyncSession, user: User) -> dict[str, list[GenreCount]]:
    result = await db.execute(
        select(MediaItem.domain, MediaItem.genres)
        .select_from(UserLibrary)
        .join(MediaItem, UserLibrary.item_id == MediaItem.id)
        .where(UserLibrary.user_id == user.id, MediaItem.genres.isnot(None))
    )
    counters: dict[str, Counter] = {domain: Counter() for domain in DOMAINS}
    for domain, genres in result.all():
        counters.setdefault(domain, Counter()).update(g for g in genres.split(",") if g)
    return {
        domain: [GenreCount(genre=genre, count=count) for genre, count in counter.most_common(5)]
        for domain, counter in counters.items()
    }


async def _consumption_over_time(db: AsyncSession, user: User) -> list[MonthlyBucket]:
    result = await db.execute(
        select(UserLibrary.completed_at, MediaItem.domain)
        .select_from(UserLibrary)
        .join(MediaItem, UserLibrary.item_id == MediaItem.id)
        .where(UserLibrary.user_id == user.id, UserLibrary.completed_at.isnot(None))
    )
    buckets: dict[str, dict[str, int]] = {}
    for completed_at, domain in result.all():
        month_key = completed_at.strftime("%Y-%m")
        bucket = buckets.setdefault(month_key, {domain_key: 0 for domain_key in DOMAINS})
        bucket[domain] += 1
    return [MonthlyBucket(month=month, **buckets[month]) for month in sorted(buckets)]


async def _avg_rating_per_domain(db: AsyncSession, user: User) -> dict[str, float | None]:
    result = await db.execute(
        select(MediaItem.domain, func.avg(Review.rating))
        .select_from(Review)
        .join(MediaItem, Review.item_id == MediaItem.id)
        .where(Review.user_id == user.id, Review.rating.isnot(None))
        .group_by(MediaItem.domain)
    )
    averages = dict(result.all())
    return {domain: (float(averages[domain]) if domain in averages else None) for domain in DOMAINS}


async def compute_stats(db: AsyncSession, user: User) -> StatsRead:
    totals = await _counts_by_domain(db, user, completed_only=True)
    added = await _counts_by_domain(db, user, completed_only=False)

    total_completed = sum(totals.values())
    total_added = sum(added.values())
    completion_rate = (total_completed / total_added) if total_added else 0.0

    created_at = user.created_at
    if created_at.tzinfo is None:
        # SQLite (used in tests) drops tzinfo from DateTime(timezone=True)
        # columns on read-back; Postgres (production) preserves it.
        created_at = created_at.replace(tzinfo=timezone.utc)
    months_since_signup = max(1.0, (datetime.now(timezone.utc) - created_at).days / 30.44)
    pace_per_domain = {domain: totals[domain] / months_since_signup for domain in DOMAINS}

    diary_dates_result = await db.execute(
        select(DiaryEntry.logged_at).where(DiaryEntry.user_id == user.id).distinct()
    )
    logged_dates = sorted(diary_dates_result.scalars().all())

    return StatsRead(
        totals=totals,
        ratings_distribution=await _ratings_distribution(db, user),
        top_genres=await _top_genres(db, user),
        consumption_over_time=await _consumption_over_time(db, user),
        avg_rating_per_domain=await _avg_rating_per_domain(db, user),
        pace_per_domain=pace_per_domain,
        completion_rate=completion_rate,
        longest_streak_days=_longest_streak(logged_dates),
    )
