from .conftest import patch_tmdb_detail as _patch_tmdb_detail


async def test_create_and_get_collection(client, auth_headers):
    resp = await client.post(
        "/collections", json={"name": "Favorites", "description": "Best of the best"}, headers=auth_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Favorites"
    assert body["is_public"] is True
    assert body["items"] == []

    get_resp = await client.get(f"/collections/{body['id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Favorites"


async def test_add_and_remove_collection_item(client, auth_headers, monkeypatch):
    _patch_tmdb_detail(monkeypatch)
    create_resp = await client.post("/collections", json={"name": "Watchlist"}, headers=auth_headers)
    collection_id = create_resp.json()["id"]

    add_resp = await client.post(
        f"/collections/{collection_id}/items",
        json={"domain": "movie", "external_id": "155", "note": "must watch"},
        headers=auth_headers,
    )
    assert add_resp.status_code == 201
    item = add_resp.json()
    assert item["position"] == 1
    assert item["note"] == "must watch"
    item_id = item["item"]["id"]

    dup_resp = await client.post(
        f"/collections/{collection_id}/items",
        json={"domain": "movie", "external_id": "155"},
        headers=auth_headers,
    )
    assert dup_resp.status_code == 409

    get_resp = await client.get(f"/collections/{collection_id}", headers=auth_headers)
    assert len(get_resp.json()["items"]) == 1

    remove_resp = await client.delete(
        f"/collections/{collection_id}/items/{item_id}", headers=auth_headers
    )
    assert remove_resp.status_code == 204

    get_resp = await client.get(f"/collections/{collection_id}", headers=auth_headers)
    assert get_resp.json()["items"] == []


async def test_update_and_delete_collection(client, auth_headers):
    create_resp = await client.post("/collections", json={"name": "Draft"}, headers=auth_headers)
    collection_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/collections/{collection_id}", json={"name": "Final", "is_public": False}, headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Final"
    assert patch_resp.json()["is_public"] is False

    delete_resp = await client.delete(f"/collections/{collection_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/collections/{collection_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_private_collection_hidden_from_other_users(client, monkeypatch):
    alice = await client.post(
        "/auth/register", json={"username": "alice", "email": "alice@example.com", "password": "password123"}
    )
    headers_alice = {"Authorization": f"Bearer {alice.json()['access_token']}"}
    create_resp = await client.post(
        "/collections", json={"name": "Secret", "is_public": False}, headers=headers_alice
    )
    collection_id = create_resp.json()["id"]

    bob = await client.post(
        "/auth/register", json={"username": "bob", "email": "bob@example.com", "password": "password123"}
    )
    headers_bob = {"Authorization": f"Bearer {bob.json()['access_token']}"}

    get_resp = await client.get(f"/collections/{collection_id}", headers=headers_bob)
    assert get_resp.status_code == 404

    patch_resp = await client.patch(
        f"/collections/{collection_id}", json={"name": "Hijacked"}, headers=headers_bob
    )
    assert patch_resp.status_code == 404

    list_resp = await client.get("/collections", params={"user_id": alice.json()["user"]["id"]}, headers=headers_bob)
    assert list_resp.json() == []

    own_list_resp = await client.get(
        "/collections", params={"user_id": alice.json()["user"]["id"]}, headers=headers_alice
    )
    assert len(own_list_resp.json()) == 1
