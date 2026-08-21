from .conftest import patch_tmdb_detail


async def _get_or_create_item(client, auth_headers, monkeypatch) -> str:
    patch_tmdb_detail(monkeypatch)
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


async def test_cannot_modify_another_users_review(client, monkeypatch):
    alice = await client.post(
        "/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "password123"}
    )
    headers_alice = {"Authorization": f"Bearer {alice.json()['access_token']}"}
    alice_item_id = await _get_or_create_item(client, headers_alice, monkeypatch)
    create_resp = await client.post(
        "/reviews", json={"item_id": alice_item_id, "rating": 4.0}, headers=headers_alice
    )
    review_id = create_resp.json()["id"]

    bob = await client.post(
        "/auth/register", json={"username": "bob", "email": "bob@example.com", "password": "password123"}
    )
    headers_bob = {"Authorization": f"Bearer {bob.json()['access_token']}"}

    patch_resp = await client.patch(f"/reviews/{review_id}", json={"rating": 1.0}, headers=headers_bob)
    assert patch_resp.status_code == 404

    delete_resp = await client.delete(f"/reviews/{review_id}", headers=headers_bob)
    assert delete_resp.status_code == 404
