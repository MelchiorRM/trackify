import uuid


async def _create_post(client, headers, body="Hello, Trackify!") -> str:
    resp = await client.post("/posts", json={"body": body}, headers=headers)
    return resp.json()["id"]


async def test_comment_crud_on_post(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)

    create_resp = await client.post(
        f"/posts/{post_id}/comments", json={"body": "Nice post!"}, headers=second_auth_headers
    )
    assert create_resp.status_code == 201
    comment = create_resp.json()
    assert comment["body"] == "Nice post!"
    assert comment["user"]["username"] == "bob"

    list_resp = await client.get(f"/posts/{post_id}/comments", headers=auth_headers)
    assert len(list_resp.json()["items"]) == 1

    update_resp = await client.patch(
        f"/comments/{comment['id']}", json={"body": "Edited"}, headers=second_auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["body"] == "Edited"

    delete_resp = await client.delete(f"/comments/{comment['id']}", headers=second_auth_headers)
    assert delete_resp.status_code == 204

    list_after = await client.get(f"/posts/{post_id}/comments", headers=auth_headers)
    assert list_after.json()["items"] == []


async def test_cannot_modify_another_users_comment(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    create_resp = await client.post(
        f"/posts/{post_id}/comments", json={"body": "Nice post!"}, headers=second_auth_headers
    )
    comment_id = create_resp.json()["id"]

    patch_resp = await client.patch(f"/comments/{comment_id}", json={"body": "Hijacked"}, headers=auth_headers)
    assert patch_resp.status_code == 404

    delete_resp = await client.delete(f"/comments/{comment_id}", headers=auth_headers)
    assert delete_resp.status_code == 404


async def test_comment_creates_notification_for_post_owner(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    await client.post(f"/posts/{post_id}/comments", json={"body": "Nice!"}, headers=second_auth_headers)

    notifications = await client.get("/notifications", headers=auth_headers)
    items = notifications.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "comment"
    assert items[0]["actor"]["username"] == "bob"


async def test_comment_mentions_notify_mentioned_user(client, auth_headers, second_auth_headers):
    post_id = await _create_post(client, auth_headers)
    await client.post(
        f"/posts/{post_id}/comments", json={"body": "cc @tester check this"}, headers=second_auth_headers
    )

    notifications = await client.get("/notifications", headers=auth_headers)
    items = notifications.json()["items"]
    types = {item["type"] for item in items}
    assert "mention" in types


async def test_comment_on_unknown_post_404s(client, auth_headers):
    resp = await client.post(
        f"/posts/{uuid.uuid4()}/comments", json={"body": "hi"}, headers=auth_headers
    )
    assert resp.status_code == 404
