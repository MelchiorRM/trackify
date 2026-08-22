from .conftest import patch_tmdb_detail


async def test_feed_empty_when_not_following_anyone(client, auth_headers):
    resp = await client.get("/feed", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []


async def test_feed_only_shows_followed_users_activity(client, auth_headers, second_auth_headers):
    third = await client.post(
        "/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "password123"},
    )
    headers_carol = {"Authorization": f"Bearer {third.json()['access_token']}"}

    await client.post("/follows/bob", headers=auth_headers)
    await client.post("/posts", json={"body": "from bob"}, headers=second_auth_headers)
    await client.post("/posts", json={"body": "from carol"}, headers=headers_carol)

    resp = await client.get("/feed", headers=auth_headers)
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "post"
    assert items[0]["actor"]["username"] == "bob"
    assert items[0]["data"]["body"] == "from bob"


async def test_feed_includes_post_review_collection_and_follow_events(
    client, auth_headers, second_auth_headers, monkeypatch
):
    patch_tmdb_detail(monkeypatch)
    await client.post("/follows/bob", headers=auth_headers)

    await client.post("/posts", json={"body": "a post"}, headers=second_auth_headers)
    item_resp = await client.post(
        "/library", json={"domain": "movie", "external_id": "155"}, headers=second_auth_headers
    )
    item_id = item_resp.json()["item"]["id"]
    await client.post("/reviews", json={"item_id": item_id, "rating": 4.5}, headers=second_auth_headers)
    await client.post("/collections", json={"name": "Bob's list"}, headers=second_auth_headers)
    await client.post("/follows/tester", headers=second_auth_headers)

    resp = await client.get("/feed", headers=auth_headers)
    types = {item["type"] for item in resp.json()["items"]}
    assert types == {"post", "library", "review", "collection", "follow"}


async def test_private_collections_excluded_from_feed(client, auth_headers, second_auth_headers):
    await client.post("/follows/bob", headers=auth_headers)
    await client.post(
        "/collections", json={"name": "Secret", "is_public": False}, headers=second_auth_headers
    )

    resp = await client.get("/feed", headers=auth_headers)
    assert resp.json()["items"] == []


async def test_feed_pagination(client, auth_headers, second_auth_headers):
    await client.post("/follows/bob", headers=auth_headers)
    for i in range(3):
        await client.post("/posts", json={"body": f"post {i}"}, headers=second_auth_headers)

    first_page = await client.get("/feed", params={"limit": 2}, headers=auth_headers)
    first_body = first_page.json()
    assert len(first_body["items"]) == 2
    assert first_body["next_cursor"] is not None

    second_page = await client.get(
        "/feed", params={"limit": 2, "cursor": first_body["next_cursor"]}, headers=auth_headers
    )
    second_body = second_page.json()
    assert len(second_body["items"]) == 1
    assert second_body["next_cursor"] is None

    seen_bodies = {item["data"]["body"] for item in first_body["items"]} | {
        item["data"]["body"] for item in second_body["items"]
    }
    assert seen_bodies == {"post 0", "post 1", "post 2"}
