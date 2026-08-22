async def _create_post(client, headers, body="Hello, Trackify!") -> str:
    resp = await client.post("/posts", json={"body": body}, headers=headers)
    return resp.json()["id"]


async def test_create_and_delete_repost(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)

    create_resp = await client.post(
        "/reposts",
        json={"target_type": "post", "target_id": post_id, "comment": "worth a read"},
        headers=second_auth_headers,
    )
    assert create_resp.status_code == 201
    repost = create_resp.json()
    assert repost["comment"] == "worth a read"
    assert repost["user"]["username"] == "bob"

    delete_resp = await client.delete(f"/reposts/{repost['id']}", headers=second_auth_headers)
    assert delete_resp.status_code == 204


async def test_duplicate_repost_conflicts(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    await client.post("/reposts", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers)
    resp = await client.post(
        "/reposts", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers
    )
    assert resp.status_code == 409


async def test_cannot_delete_another_users_repost(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    create_resp = await client.post(
        "/reposts", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers
    )
    repost_id = create_resp.json()["id"]

    resp = await client.delete(f"/reposts/{repost_id}", headers=auth_headers)
    assert resp.status_code == 404


async def test_repost_creates_notification_for_original_author(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    await client.post("/reposts", json={"target_type": "post", "target_id": post_id}, headers=second_auth_headers)

    notifications = await client.get("/notifications", headers=auth_headers)
    items = notifications.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "repost"
    assert items[0]["actor"]["username"] == "bob"
