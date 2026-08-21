import uuid

from .conftest import patch_tmdb_detail


async def _create_items(client, auth_headers, monkeypatch, external_ids):
    patch_tmdb_detail(monkeypatch)
    item_ids = []
    for external_id in external_ids:
        resp = await client.get(f"/items/movie/{external_id}", headers=auth_headers)
        item_ids.append(resp.json()["id"])
    return item_ids


async def test_set_favorites_replaces_and_orders(client, auth_headers, monkeypatch):
    item_ids = await _create_items(client, auth_headers, monkeypatch, ["1", "2", "3"])

    resp = await client.put("/users/me/favorites", json={"item_ids": item_ids}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert [f["position"] for f in body] == [1, 2, 3]
    assert [f["item"]["id"] for f in body] == item_ids

    # Replacing with a smaller set drops the old rows entirely.
    resp = await client.put(
        "/users/me/favorites", json={"item_ids": [item_ids[1]]}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["position"] == 1
    assert body[0]["item"]["id"] == item_ids[1]


async def test_favorites_reject_more_than_four(client, auth_headers, monkeypatch):
    item_ids = await _create_items(client, auth_headers, monkeypatch, ["1", "2", "3", "4", "5"])
    resp = await client.put("/users/me/favorites", json={"item_ids": item_ids}, headers=auth_headers)
    assert resp.status_code == 422


async def test_favorites_reject_duplicate_items(client, auth_headers, monkeypatch):
    item_ids = await _create_items(client, auth_headers, monkeypatch, ["1"])
    resp = await client.put(
        "/users/me/favorites", json={"item_ids": [item_ids[0], item_ids[0]]}, headers=auth_headers
    )
    assert resp.status_code == 422


async def test_favorites_reject_unknown_item(client, auth_headers):
    resp = await client.put(
        "/users/me/favorites", json={"item_ids": [str(uuid.uuid4())]}, headers=auth_headers
    )
    assert resp.status_code == 404
