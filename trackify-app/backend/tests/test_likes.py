import uuid


async def _create_post(client, headers, body="Hello, Trackify!") -> str:
    resp = await client.post("/posts", json={"body": body}, headers=headers)
    return resp.json()["id"]


async def test_like_and_unlike_post(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)

    like_resp = await client.post(
        "/likes", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers
    )
    assert like_resp.status_code == 201
    assert like_resp.json()["user"]["username"] == "bob"

    list_resp = await client.get(
        "/likes", params={"target_type": "post", "target_id": post_id}, headers=auth_headers
    )
    assert len(list_resp.json()["items"]) == 1

    unlike_resp = await client.request(
        "DELETE",
        "/likes",
        json={"target_type": "post", "target_id": post_id},
        headers=second_auth_headers,
    )
    assert unlike_resp.status_code == 204

    list_after = await client.get(
        "/likes", params={"target_type": "post", "target_id": post_id}, headers=auth_headers
    )
    assert list_after.json()["items"] == []


async def test_duplicate_like_conflicts(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    await client.post("/likes", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers)
    resp = await client.post(
        "/likes", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers
    )
    assert resp.status_code == 409


async def test_unlike_when_not_liked_404s(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    resp = await client.request(
        "DELETE", "/likes", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers
    )
    assert resp.status_code == 404


async def test_like_creates_notification_but_not_for_self_like(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)

    await client.post("/likes", json={"target_type": "post", "target_id": post_id}, headers=auth_headers)
    self_like_notifications = await client.get("/notifications", headers=auth_headers)
    assert self_like_notifications.json()["items"] == []

    await client.post("/likes", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers)
    notifications = await client.get("/notifications", headers=auth_headers)
    items = notifications.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "like"
    assert items[0]["actor"]["username"] == "bob"


async def test_like_unknown_target_404s(client, auth_headers):
    resp = await client.post(
        "/likes", json={"target_type": "post", "target_id": str(uuid.uuid4())}, headers=auth_headers
    )
    assert resp.status_code == 404
