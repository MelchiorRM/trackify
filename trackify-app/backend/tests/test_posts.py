import uuid


async def test_create_get_delete_post(client, auth_headers):
    create_resp = await client.post("/posts", json={"body": "Hello, Trackify!"}, headers=auth_headers)
    assert create_resp.status_code == 201
    post = create_resp.json()
    assert post["body"] == "Hello, Trackify!"
    assert post["user"]["username"] == "tester"

    get_resp = await client.get(f"/posts/{post['id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == post["id"]

    delete_resp = await client.delete(f"/posts/{post['id']}", headers=auth_headers)
    assert delete_resp.status_code == 204

    get_after = await client.get(f"/posts/{post['id']}", headers=auth_headers)
    assert get_after.status_code == 404


async def test_cannot_delete_another_users_post(client, auth_headers, second_auth_headers):
    create_resp = await client.post("/posts", json={"body": "Hello!"}, headers=auth_headers)
    post_id = create_resp.json()["id"]

    resp = await client.delete(f"/posts/{post_id}", headers=second_auth_headers)
    assert resp.status_code == 404


async def test_post_body_too_long_rejected(client, auth_headers):
    resp = await client.post("/posts", json={"body": "x" * 501}, headers=auth_headers)
    assert resp.status_code == 422


async def test_get_unknown_post_404s(client, auth_headers):
    resp = await client.get(f"/posts/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


async def test_post_mentions_notify_mentioned_user(client, auth_headers, second_auth_headers):
    await client.post("/posts", json={"body": "hey @bob check this out"}, headers=auth_headers)

    notifications = await client.get("/notifications", headers=second_auth_headers)
    items = notifications.json()["items"]
    assert len(items) == 1
    assert items[0]["type"] == "mention"
    assert items[0]["actor"]["username"] == "tester"


async def test_user_posts_listed_on_profile(client, auth_headers):
    await client.post("/posts", json={"body": "first"}, headers=auth_headers)
    await client.post("/posts", json={"body": "second"}, headers=auth_headers)

    resp = await client.get("/users/tester/posts", headers=auth_headers)
    assert resp.status_code == 200
    bodies = [p["body"] for p in resp.json()["items"]]
    assert bodies == ["second", "first"]
