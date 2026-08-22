async def test_unread_count_and_mark_read(client, auth_headers, second_auth_headers):
    await client.post("/follows/tester", headers=second_auth_headers)

    unread_resp = await client.get("/notifications/unread-count", headers=auth_headers)
    assert unread_resp.json()["count"] == 1

    list_resp = await client.get("/notifications", headers=auth_headers)
    notification_id = list_resp.json()["items"][0]["id"]

    mark_resp = await client.patch(f"/notifications/{notification_id}/read", headers=auth_headers)
    assert mark_resp.status_code == 200
    assert mark_resp.json()["read"] is True

    unread_after = await client.get("/notifications/unread-count", headers=auth_headers)
    assert unread_after.json()["count"] == 0


async def test_mark_all_read(client, auth_headers, second_auth_headers):
    await client.post("/follows/tester", headers=second_auth_headers)
    post_resp = await client.post("/posts", json={"body": "hi"}, headers=auth_headers)
    await client.post(
        "/likes", json={"target_type": "post", "target_id": post_resp.json()["id"]}, headers=second_auth_headers
    )

    unread_resp = await client.get("/notifications/unread-count", headers=auth_headers)
    assert unread_resp.json()["count"] == 2

    mark_all_resp = await client.post("/notifications/read-all", headers=auth_headers)
    assert mark_all_resp.status_code == 204

    unread_after = await client.get("/notifications/unread-count", headers=auth_headers)
    assert unread_after.json()["count"] == 0


async def test_unread_only_filter(client, auth_headers, second_auth_headers):
    await client.post("/follows/tester", headers=second_auth_headers)
    list_resp = await client.get("/notifications", headers=auth_headers)
    notification_id = list_resp.json()["items"][0]["id"]
    await client.patch(f"/notifications/{notification_id}/read", headers=auth_headers)

    unread_only_resp = await client.get(
        "/notifications", params={"unread_only": True}, headers=auth_headers
    )
    assert unread_only_resp.json()["items"] == []


async def test_cannot_mark_another_users_notification_read(client, auth_headers, second_auth_headers):
    await client.post("/follows/tester", headers=second_auth_headers)
    list_resp = await client.get("/notifications", headers=auth_headers)
    notification_id = list_resp.json()["items"][0]["id"]

    resp = await client.patch(f"/notifications/{notification_id}/read", headers=second_auth_headers)
    assert resp.status_code == 404
