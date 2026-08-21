from datetime import datetime, timezone

from .conftest import patch_tmdb_detail


async def _add_and_complete(client, auth_headers, external_id) -> str:
    add_resp = await client.post(
        "/library", json={"domain": "movie", "external_id": external_id}, headers=auth_headers
    )
    library_id = add_resp.json()["id"]
    await client.patch(f"/library/{library_id}", json={"status": "completed"}, headers=auth_headers)
    return add_resp.json()["item"]["id"]


async def test_stats_totals_ratings_avg_and_completion(client, auth_headers, monkeypatch):
    patch_tmdb_detail(monkeypatch)

    item1 = await _add_and_complete(client, auth_headers, "1")
    item2 = await _add_and_complete(client, auth_headers, "2")
    # A third item added but never completed, to exercise completion_rate.
    await client.post("/library", json={"domain": "movie", "external_id": "3"}, headers=auth_headers)

    await client.post("/reviews", json={"item_id": item1, "rating": 5.0}, headers=auth_headers)
    await client.post("/reviews", json={"item_id": item2, "rating": 3.0}, headers=auth_headers)

    resp = await client.get("/stats/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert body["totals"] == {"movie": 2, "book": 0, "music": 0}
    assert body["ratings_distribution"]["5"] == 1
    assert body["ratings_distribution"]["3"] == 1
    assert body["avg_rating_per_domain"]["movie"] == 4.0
    assert body["avg_rating_per_domain"]["book"] is None
    assert body["completion_rate"] == 2 / 3


async def test_stats_longest_streak(client, auth_headers, monkeypatch):
    patch_tmdb_detail(monkeypatch)
    add_resp = await client.post("/library", json={"domain": "movie", "external_id": "1"}, headers=auth_headers)
    library_id = add_resp.json()["id"]

    for logged_at in ("2024-01-01", "2024-01-02", "2024-01-03"):
        await client.post(
            f"/library/{library_id}/diary",
            json={"logged_at": logged_at, "rewatch": True},
            headers=auth_headers,
        )
    # A separate, non-adjacent day shouldn't extend the streak.
    await client.post(
        f"/library/{library_id}/diary",
        json={"logged_at": "2024-01-06", "rewatch": True},
        headers=auth_headers,
    )

    resp = await client.get("/stats/me", headers=auth_headers)
    assert resp.json()["longest_streak_days"] == 3


async def test_stats_consumption_over_time_includes_current_month(client, auth_headers, monkeypatch):
    patch_tmdb_detail(monkeypatch)
    await _add_and_complete(client, auth_headers, "1")

    resp = await client.get("/stats/me", headers=auth_headers)
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    buckets = {b["month"]: b for b in resp.json()["consumption_over_time"]}
    assert current_month in buckets
    assert buckets[current_month]["movie"] == 1
