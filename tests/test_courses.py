from httpx import AsyncClient

from tests.conftest import register_and_login


async def test_course_crud_and_archive(client: AsyncClient) -> None:
    headers = await register_and_login(client)

    created = await client.post(
        "/api/v1/courses",
        headers=headers,
        json={
            "name": "FastAPI 入门",
            "description": "从路由到数据库",
            "color": "#6657e8",
        },
    )
    assert created.status_code == 201
    course_id = created.json()["id"]

    listed = await client.get("/api/v1/courses", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["name"] == "FastAPI 入门"

    updated = await client.patch(
        f"/api/v1/courses/{course_id}",
        headers=headers,
        json={"name": "FastAPI 实战", "is_archived": True},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "FastAPI 实战"

    hidden = await client.get("/api/v1/courses", headers=headers)
    assert hidden.json()["total"] == 0

    with_archived = await client.get(
        "/api/v1/courses?include_archived=true",
        headers=headers,
    )
    assert with_archived.json()["total"] == 1
    assert with_archived.json()["items"][0]["is_archived"] is True


async def test_users_cannot_access_each_others_courses(client: AsyncClient) -> None:
    alice_headers = await register_and_login(
        client,
        username="alice2",
        email="alice2@example.com",
    )
    bob_headers = await register_and_login(
        client,
        username="bob2",
        email="bob2@example.com",
    )

    created = await client.post(
        "/api/v1/courses",
        headers=alice_headers,
        json={"name": "Alice 的项目"},
    )
    course_id = created.json()["id"]

    response = await client.get(f"/api/v1/courses/{course_id}", headers=bob_headers)
    assert response.status_code == 404

    bob_list = await client.get("/api/v1/courses", headers=bob_headers)
    assert bob_list.json()["total"] == 0