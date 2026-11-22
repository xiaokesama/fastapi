from httpx import AsyncClient

from tests.conftest import register_and_login


async def test_register_login_and_me(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "Alice@Example.com",
            "password": "strong-password",
        },
    )
    assert register_response.status_code == 201
    body = register_response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "password" not in body

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "ALICE", "password": "strong-password"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "alice"


async def test_registration_conflict_and_bad_login(client: AsyncClient) -> None:
    await register_and_login(client, username="bob", email="bob@example.com")

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "BOB",
            "email": "another@example.com",
            "password": "password123",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "conflict"

    wrong_password = await client.post(
        "/api/v1/auth/login",
        data={"username": "bob", "password": "not-the-password"},
    )
    assert wrong_password.status_code == 401
    assert wrong_password.headers["www-authenticate"] == "Bearer"


async def test_me_requires_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401