from httpx import AsyncClient

from tests.conftest import register_and_login


async def create_course(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.post(
        "/api/v1/courses",
        headers=headers,
        json={"name": "Python 异步编程"},
    )
    assert response.status_code == 201
    return response.json()["id"]


async def test_task_lifecycle_and_filters(client: AsyncClient) -> None:
    headers = await register_and_login(client)
    course_id = await create_course(client, headers)

    response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "course_id": course_id,
            "title": "理解 async / await",
            "priority": "high",
            "estimated_minutes": 45,
        },
    )
    assert response.status_code == 201
    task = response.json()
    assert task["status"] == "todo"
    assert task["completed_at"] is None

    filtered = await client.get(
        f"/api/v1/tasks?course_id={course_id}&status=todo&priority=high",
        headers=headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1

    completed = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"status": "done"},
    )
    assert completed.status_code == 200
    assert completed.json()["completed_at"] is not None

    done_only = await client.get(
        "/api/v1/tasks?status=done",
        headers=headers,
    )
    assert done_only.json()["total"] == 1

    reopened = await client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"status": "in_progress"},
    )
    assert reopened.json()["completed_at"] is None

    deleted = await client.delete(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert deleted.status_code == 204

    empty = await client.get("/api/v1/tasks", headers=headers)
    assert empty.json()["total"] == 0


async def test_task_validation_and_ownership(client: AsyncClient) -> None:
    alice_headers = await register_and_login(
        client,
        username="alice3",
        email="alice3@example.com",
    )
    bob_headers = await register_and_login(
        client,
        username="bob3",
        email="bob3@example.com",
    )
    course_id = await create_course(client, alice_headers)

    empty_title = await client.post(
        "/api/v1/tasks",
        headers=alice_headers,
        json={"course_id": course_id, "title": "   "},
    )
    assert empty_title.status_code == 422

    missing_course = await client.post(
        "/api/v1/tasks",
        headers=alice_headers,
        json={"course_id": 9999, "title": "不存在的项目"},
    )
    assert missing_course.status_code == 404

    bob_create = await client.post(
        "/api/v1/tasks",
        headers=bob_headers,
        json={"course_id": course_id, "title": "越权任务"},
    )
    assert bob_create.status_code == 404