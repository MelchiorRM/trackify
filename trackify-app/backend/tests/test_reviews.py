import app.external.tmdb as tmdb


async def _fake_tmdb_detail(tmdb_id):
    return {
        "id": int(tmdb_id),
        "title": "The Dark Knight",
        "release_date": "2008-07-16",
        "genres": [{"id": 28, "name": "Action"}],
        "overview": "Batman raises the stakes...",
        "poster_path": "/poster.jpg",
        "popularity": 84.2,
        "credits": {"crew": [{"job": "Director", "name": "Christopher Nolan"}]},
    }


async def _get_or_create_item(client, auth_headers, monkeypatch) -> str:
    monkeypatch.setattr(tmdb, "get_movie", _fake_tmdb_detail)
    resp = await client.get("/items/movie/155", headers=auth_headers)
    return resp.json()["id"]


async def test_create_review(client, auth_headers, monkeypatch):
    item_id = await _get_or_create_item(client, auth_headers, monkeypatch)
    resp = await client.post(
        "/reviews", json={"item_id": item_id, "rating": 4.5, "body": "Great movie"}, headers=auth_headers
    )
    assert resp.status_code == 201
    assert resp.json()["rating"] == 4.5


async def test_review_requires_auth(client, auth_headers, monkeypatch):
    item_id = await _get_or_create_item(client, auth_headers, monkeypatch)
    resp = await client.post("/reviews", json={"item_id": item_id, "rating": 4.5})
    assert resp.status_code == 401


async def test_duplicate_review_conflicts(client, auth_headers, monkeypatch):
    item_id = await _get_or_create_item(client, auth_headers, monkeypatch)
    await client.post("/reviews", json={"item_id": item_id, "rating": 4.5}, headers=auth_headers)
    resp = await client.post("/reviews", json={"item_id": item_id, "rating": 3.0}, headers=auth_headers)
    assert resp.status_code == 409


async def test_list_reviews_for_item_is_public(client, auth_headers, monkeypatch):
    item_id = await _get_or_create_item(client, auth_headers, monkeypatch)
    await client.post("/reviews", json={"item_id": item_id, "rating": 5.0}, headers=auth_headers)

    resp = await client.get("/reviews", params={"item_id": item_id})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_update_and_delete_review(client, auth_headers, monkeypatch):
    item_id = await _get_or_create_item(client, auth_headers, monkeypatch)
    create_resp = await client.post("/reviews", json={"item_id": item_id, "rating": 3.0}, headers=auth_headers)
    review_id = create_resp.json()["id"]

    patch_resp = await client.patch(f"/reviews/{review_id}", json={"rating": 4.0}, headers=auth_headers)
    assert patch_resp.json()["rating"] == 4.0

    delete_resp = await client.delete(f"/reviews/{review_id}", headers=auth_headers)
    assert delete_resp.status_code == 204
