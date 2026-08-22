async def test_follow_and_unfollow(client, auth_headers, second_auth_headers):
    resp = await client.post("/follows/bob", headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["user"]["username"] == "bob"

    followers = await client.get("/follows/followers", params={"username": "bob"}, headers=auth_headers)
    assert [f["user"]["username"] for f in followers.json()["items"]] == ["tester"]

    following = await client.get("/follows/following", headers=auth_headers)
    assert [f["user"]["username"] for f in following.json()["items"]] == ["bob"]

    unfollow_resp = await client.delete("/follows/bob", headers=auth_headers)
    assert unfollow_resp.status_code == 204

    following_after = await client.get("/follows/following", headers=auth_headers)
    assert following_after.json()["items"] == []


async def test_cannot_follow_self(client, auth_headers):
    resp = await client.post("/follows/tester", headers=auth_headers)
    assert resp.status_code == 422


async def test_duplicate_follow_conflicts(client, auth_headers, second_auth_headers):
    await client.post("/follows/bob", headers=auth_headers)
    resp = await client.post("/follows/bob", headers=auth_headers)
    assert resp.status_code == 409


async def test_unfollow_when_not_following_404s(client, auth_headers, second_auth_headers):
    resp = await client.delete("/follows/bob", headers=auth_headers)
    assert resp.status_code == 404


async def test_follow_creates_notification(client, auth_headers, second_auth_headers):
    await client.post("/follows/bob", headers=auth_headers)

    notifications = await client.get("/notifications", headers=second_auth_headers)
    assert notifications.status_code == 200
    items = notifications.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "follow"
    assert items[0]["actor"]["username"] == "tester"
