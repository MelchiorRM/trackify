from pydantic import BaseModel


class GenreCount(BaseModel):
    genre: str
    count: int


class MonthlyBucket(BaseModel):
    month: str  # "YYYY-MM"
    movie: int
    book: int
    music: int


class StatsRead(BaseModel):
    totals: dict[str, int]  # completed count per domain
    ratings_distribution: dict[int, int]  # star (1-5) -> count
    top_genres: dict[str, list[GenreCount]]  # domain -> top 5 genres
    consumption_over_time: list[MonthlyBucket]  # completed_at, monthly, oldest first
    avg_rating_per_domain: dict[str, float | None]
    pace_per_domain: dict[str, float]  # completed items per month since signup
    completion_rate: float  # completed / total added, across all domains
    longest_streak_days: int  # longest run of consecutive days with a diary entry
