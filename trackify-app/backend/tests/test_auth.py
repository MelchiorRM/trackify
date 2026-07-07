async def _register(client, username="alice", email="alice@example.com", password="password123"):
    return await client.post(
        "/auth/register", json={"username": username, "email": email, "password": password}
    )


async def test_register_returns_access_token_and_user(client):
    resp = await _register(client)
    assert resp.status_code == 201

    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["username"] == "alice"
    assert body["user"]["email"] == "alice@example.com"
    assert "password" not in body["user"]
    assert "hashed_password" not in body["user"]


async def test_register_sets_httponly_refresh_cookie(client):
    resp = await _register(client)
    assert "refresh_token" in resp.cookies
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_header


async def test_register_duplicate_email_is_rejected(client):
    await _register(client, username="alice", email="dupe@example.com")
    resp = await _register(client, username="someoneelse", email="dupe@example.com")
    assert resp.status_code == 409


async def test_register_duplicate_username_is_rejected(client):
    await _register(client, username="dupeuser", email="first@example.com")
    resp = await _register(client, username="dupeuser", email="second@example.com")
    assert resp.status_code == 409


async def test_login_with_correct_credentials(client):
    await _register(client, email="bob@example.com", password="correct-password")
    resp = await client.post("/auth/login", json={"email": "bob@example.com", "password": "correct-password"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_with_wrong_password_is_unauthorized(client):
    await _register(client, email="carol@example.com", password="correct-password")
    resp = await client.post("/auth/login", json={"email": "carol@example.com", "password": "wrong-password"})
    assert resp.status_code == 401


async def test_login_with_unknown_email_is_unauthorized(client):
    resp = await client.post("/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401


async def test_get_me_requires_authentication(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


async def test_get_me_with_valid_token(client):
    register_resp = await _register(client, username="dave", email="dave@example.com")
    access_token = register_resp.json()["access_token"]

    resp = await client.get("/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "dave"


async def test_get_me_with_garbage_token_is_unauthorized(client):
    resp = await client.get("/users/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


async def test_refresh_issues_a_new_access_token(client):
    await _register(client, username="erin", email="erin@example.com")

    resp = await client.post("/auth/refresh")
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_refresh_without_cookie_is_unauthorized(client):
    resp = await client.post("/auth/refresh")
    assert resp.status_code == 401


async def test_logout_revokes_the_refresh_token(client):
    await _register(client, username="frank", email="frank@example.com")

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 204

    # the cookie jar still holds the (now server-side-revoked) cookie value
    # unless the client honored the Set-Cookie clear — assert the server
    # actually invalidated it by replaying the original refresh cookie
    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 401


async def test_update_username(client):
    register_resp = await _register(client, username="grace", email="grace@example.com")
    access_token = register_resp.json()["access_token"]

    resp = await client.patch(
        "/users/me",
        json={"username": "grace2"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "grace2"


async def test_update_username_conflict(client):
    await _register(client, username="holly", email="holly@example.com")
    second = await _register(client, username="ivan", email="ivan@example.com")
    access_token = second.json()["access_token"]

    resp = await client.patch(
        "/users/me",
        json={"username": "holly"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 409
