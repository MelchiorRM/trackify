from .conftest import patch_tmdb_detail


async def test_public_profile_404_for_unknown_user(client, auth_headers):
    resp = await client.get("/users/nobody", headers=auth_headers)
    assert resp.status_code == 404


async def test_public_profile_includes_favorites(client, auth_headers, monkeypatch):
    patch_tmdb_detail(monkeypatch)
    item_resp = await client.get("/items/movie/1", headers=auth_headers)
    item_id = item_resp.json()["id"]
    await client.put("/users/me/favorites", json={"item_ids": [item_id]}, headers=auth_headers)

    resp = await client.get("/users/tester", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "tester"
    assert len(body["favorites"]) == 1
    assert body["favorites"][0]["item"]["id"] == item_id


async def test_public_library_and_reviews_visible_to_others(client, monkeypatch):
    patch_tmdb_detail(monkeypatch)
    alice = await client.post(
        "/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "password123"}
    )
    headers_alice = {"Authorization": f"Bearer {alice.json()['access_token']}"}
    add_resp = await client.post(
        "/library", json={"domain": "movie", "external_id": "1"}, headers=headers_alice
    )
    item_id = add_resp.json()["item"]["id"]
    await client.post("/reviews", json={"item_id": item_id, "rating": 4.5}, headers=headers_alice)

    bob = await client.post(
        "/auth/register", json={"username": "bob", "email": "bob@example.com", "password": "password123"}
    )
    headers_bob = {"Authorization": f"Bearer {bob.json()['access_token']}"}

    library_resp = await client.get("/users/alice/library", headers=headers_bob)
    assert library_resp.status_code == 200
    assert len(library_resp.json()) == 1

    reviews_resp = await client.get("/users/alice/reviews", headers=headers_bob)
    assert reviews_resp.status_code == 200
    assert reviews_resp.json()[0]["rating"] == 4.5


async def test_public_collections_only_show_public_ones_to_others(client):
    alice = await client.post(
        "/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "password123"}
    )
    headers_alice = {"Authorization": f"Bearer {alice.json()['access_token']}"}
    await client.post("/collections", json={"name": "Public list"}, headers=headers_alice)
    await client.post(
        "/collections", json={"name": "Private list", "is_public": False}, headers=headers_alice
    )

    bob = await client.post(
        "/auth/register", json={"username": "bob", "email": "bob@example.com", "password": "password123"}
    )
    headers_bob = {"Authorization": f"Bearer {bob.json()['access_token']}"}

    resp = await client.get("/users/alice/collections", headers=headers_bob)
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert names == ["Public list"]

    own_resp = await client.get("/users/alice/collections", headers=headers_alice)
    assert len(own_resp.json()) == 2


async def test_public_diary_pagination(client, auth_headers, monkeypatch):
    patch_tmdb_detail(monkeypatch)
    add_resp = await client.post("/library", json={"domain": "movie", "external_id": "1"}, headers=auth_headers)
    library_id = add_resp.json()["id"]

    for logged_at in ("2024-01-01", "2024-01-02", "2024-01-03"):
        await client.post(
            f"/library/{library_id}/diary",
            json={"logged_at": logged_at, "rewatch": True},
            headers=auth_headers,
        )

    first_page = await client.get("/users/tester/diary", params={"limit": 2}, headers=auth_headers)
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert len(first_body["entries"]) == 2
    assert first_body["next_cursor"] is not None

    second_page = await client.get(
        "/users/tester/diary", params={"limit": 2, "cursor": first_body["next_cursor"]}, headers=auth_headers
    )
    second_body = second_page.json()
    assert len(second_body["entries"]) == 1
    assert second_body["next_cursor"] is None

    seen_ids = {e["id"] for e in first_body["entries"]} | {e["id"] for e in second_body["entries"]}
    assert len(seen_ids) == 3
