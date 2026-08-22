async def test_conversation_thread_reused_across_calls(client, auth_headers, second_auth_headers):
    first = await client.post("/conversations/bob", headers=auth_headers)
    assert first.status_code == 200
    second = await client.post("/conversations/tester", headers=second_auth_headers)
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


async def test_cannot_message_self(client, auth_headers):
    resp = await client.post("/conversations/tester", headers=auth_headers)
    assert resp.status_code == 422


async def test_send_and_list_messages(client, auth_headers, second_auth_headers):
    start_resp = await client.post("/conversations/bob", headers=auth_headers)
    conversation_id = start_resp.json()["id"]

    send_resp = await client.post(
        f"/conversations/{conversation_id}/messages", json={"body": "hey bob"}, headers=auth_headers
    )
    assert send_resp.status_code == 201
    assert send_resp.json()["sender"]["username"] == "tester"

    reply_resp = await client.post(
        f"/conversations/{conversation_id}/messages", json={"body": "hey tester"}, headers=second_auth_headers
    )
    assert reply_resp.status_code == 201

    list_resp = await client.get(f"/conversations/{conversation_id}/messages", headers=auth_headers)
    bodies = [m["body"] for m in list_resp.json()["items"]]
    assert bodies == ["hey tester", "hey bob"]


async def test_messages_do_not_create_notifications(client, auth_headers, second_auth_headers):
    start_resp = await client.post("/conversations/bob", headers=auth_headers)
    conversation_id = start_resp.json()["id"]
    await client.post(
        f"/conversations/{conversation_id}/messages", json={"body": "hey bob"}, headers=auth_headers
    )

    notifications = await client.get("/notifications", headers=second_auth_headers)
    assert notifications.json()["items"] == []


async def test_unread_count_and_mark_read(client, auth_headers, second_auth_headers):
    start_resp = await client.post("/conversations/bob", headers=auth_headers)
    conversation_id = start_resp.json()["id"]
    await client.post(
        f"/conversations/{conversation_id}/messages", json={"body": "hey bob"}, headers=auth_headers
    )

    unread_resp = await client.get("/conversations/unread-count", headers=second_auth_headers)
    assert unread_resp.json()["count"] == 1

    conversations_resp = await client.get("/conversations", headers=second_auth_headers)
    conversation = conversations_resp.json()["items"][0]
    assert conversation["unread_count"] == 1
    assert conversation["last_message"]["body"] == "hey bob"
    assert conversation["other_user"]["username"] == "tester"

    mark_resp = await client.post(f"/conversations/{conversation_id}/read", headers=second_auth_headers)
    assert mark_resp.status_code == 204

    unread_after = await client.get("/conversations/unread-count", headers=second_auth_headers)
    assert unread_after.json()["count"] == 0


async def test_cannot_access_conversation_youre_not_part_of(client, auth_headers, second_auth_headers):
    start_resp = await client.post("/conversations/bob", headers=auth_headers)
    conversation_id = start_resp.json()["id"]

    third = await client.post(
        "/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "password123"},
    )
    headers_carol = {"Authorization": f"Bearer {third.json()['access_token']}"}

    resp = await client.get(f"/conversations/{conversation_id}/messages", headers=headers_carol)
    assert resp.status_code == 404
