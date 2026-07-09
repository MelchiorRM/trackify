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


def _patch_tmdb_detail(monkeypatch):
    monkeypatch.setattr(tmdb, "get_movie", _fake_tmdb_detail)


async def test_get_item_creates_media_item_on_first_view(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    resp = await client.get("/items/movie/155", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "The Dark Knight"
    assert body["creator"] == "Christopher Nolan"
    assert "Action" in body["genres"]


async def test_get_item_twice_only_fetches_upstream_once(client, auth_headers, monkeypatch):
    calls = 0

    async def counting_detail(tmdb_id):
        nonlocal calls
        calls += 1
        return await _fake_tmdb_detail(tmdb_id)

    monkeypatch.setattr(tmdb, "get_movie", counting_detail)
    await client.get("/items/movie/155", headers=auth_headers)
    await client.get("/items/movie/155", headers=auth_headers)
    assert calls == 1


async def test_get_unknown_item_404s(client, auth_headers, monkeypatch):
    async def fail(tmdb_id):
        raise RuntimeError("not found upstream")

    monkeypatch.setattr(tmdb, "get_movie", fail)
    resp = await client.get("/items/movie/999999", headers=auth_headers)
    assert resp.status_code == 404


async def test_add_to_library_creates_entry(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    resp = await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "want"
    assert body["item"]["title"] == "The Dark Knight"


async def test_add_duplicate_to_library_conflicts(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=auth_headers)
    resp = await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=auth_headers)
    assert resp.status_code == 409


async def test_list_library_filters_by_domain(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=auth_headers)

    movies = await client.get("/library", params={"domain": "movie"}, headers=auth_headers)
    assert len(movies.json()) == 1
    books = await client.get("/library", params={"domain": "book"}, headers=auth_headers)
    assert len(books.json()) == 0


async def test_completing_an_item_autologs_a_diary_entry(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    add_resp = await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=auth_headers)
    library_id = add_resp.json()["id"]

    patch_resp = await client.patch(f"/library/{library_id}", json={"status": "completed"}, headers=auth_headers)
    assert patch_resp.status_code == 200
    assert patch_resp.json()["completed_at"] is not None

    diary_resp = await client.get(f"/library/{library_id}/diary", headers=auth_headers)
    entries = diary_resp.json()
    assert len(entries) == 1
    assert entries[0]["rewatch"] is False


async def test_explicit_rewatch_diary_entry(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    add_resp = await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=auth_headers)
    library_id = add_resp.json()["id"]

    resp = await client.post(
        f"/library/{library_id}/diary",
        json={"logged_at": "2024-01-01", "rewatch": True, "rating": 4.5},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["rewatch"] is True


async def test_delete_library_entry(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    add_resp = await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=auth_headers)
    library_id = add_resp.json()["id"]

    resp = await client.delete(f"/library/{library_id}", headers=auth_headers)
    assert resp.status_code == 204
    assert (await client.get("/library", headers=auth_headers)).json() == []


async def test_cannot_modify_another_users_library_entry(client, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    alice = await client.post(
        "/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "password123"}
    )
    headers_alice = {"Authorization": f"Bearer {alice.json()['access_token']}"}
    add_resp = await client.post(
        "/library", json={"domain": "movie", "external_id": "155"}, headers=headers_alice
    )
    library_id = add_resp.json()["id"]

    bob = await client.post(
        "/auth/register", json={"username": "bob", "email": "bob@example.com", "password": "password123"}
    )
    headers_bob = {"Authorization": f"Bearer {bob.json()['access_token']}"}
    resp = await client.patch(f"/library/{library_id}", json={"status": "completed"}, headers=headers_bob)
    assert resp.status_code == 404


async def test_cannot_delete_another_users_diary_entry(client, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    alice = await client.post(
        "/auth/register", json={"username": "alice2", "email": "alice2@example.com", "password": "password123"}
    )
    headers_alice = {"Authorization": f"Bearer {alice.json()['access_token']}"}
    add_resp = await client.post("/library", json={"domain": "movie", "external_id": "155"}, headers=headers_alice)
    library_id = add_resp.json()["id"]
    diary_resp = await client.post(
        f"/library/{library_id}/diary",
        json={"logged_at": "2024-01-01", "rewatch": True},
        headers=headers_alice,
    )
    entry_id = diary_resp.json()["id"]

    bob = await client.post(
        "/auth/register", json={"username": "bob2", "email": "bob2@example.com", "password": "password123"}
    )
    headers_bob = {"Authorization": f"Bearer {bob.json()['access_token']}"}
    resp = await client.delete(f"/diary/{entry_id}", headers=headers_bob)
    assert resp.status_code == 404

    still_there = await client.get(f"/library/{library_id}/diary", headers=headers_alice)
    assert len(still_there.json()) == 1
