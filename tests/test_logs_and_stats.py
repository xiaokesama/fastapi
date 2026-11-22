from datetime import date, timedelta

from httpx import AsyncClient

from tests.conftest import register_and_login


async def test_study_logs_and_stats(client: AsyncClient) -> None:
    headers = await register_and_login(client)
    course_response = await client.post(
        "/api/v1/courses",
        headers=headers,
        json={"name": "SQLAlchemy"},
    )
    course_id = course_response.json()["id"]

    task_response = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"course_id": course_id, "title": "关系映射"},
    )
    task_id = task_response.json()["id"]

    today = date.today()
    yesterday = today - timedelta(days=1)
    first = await client.post(
        "/api/v1/study-logs",
        headers=headers,
        json={
            "course_id": course_id,
            "task_id": task_id,
            "minutes": 40,
            "studied_on": yesterday.isoformat(),
            "note": "练习 relationship",
        },
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/study-logs",
        headers=headers,
        json={
            "course_id": course_id,
            "minutes": 25,
            "studied_on": today.isoformat(),
            "note": "复习查询",
        },
    )
    assert second.status_code == 201

    logs = await client.get("/api/v1/study-logs", headers=headers)
    assert logs.status_code == 200
    assert logs.json()["total"] == 2

    stats = await client.get("/api/v1/stats/overview?days=14", headers=headers)
    assert stats.status_code == 200
    stats_body = stats.json()
    assert stats_body["total_minutes"] == 65
    assert stats_body["today_minutes"] == 25
    assert stats_body["current_streak"] == 2
    assert len(stats_body["daily_minutes"]) == 14

    course_stats = await client.get("/api/v1/stats/courses", headers=headers)
    assert course_stats.status_code == 200
    assert course_stats.json()[0]["minutes"] == 65
    assert course_stats.json()[0]["total_tasks"] == 1


async def test_log_requires_matching_task_course(client: AsyncClient) -> None:
    headers = await register_and_login(client)
    first_course = await client.post(
        "/api/v1/courses",
        headers=headers,
        json={"name": "课程 A"},
    )
    second_course = await client.post(
        "/api/v1/courses",
        headers=headers,
        json={"name": "课程 B"},
    )
    task = await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"course_id": first_course.json()["id"], "title": "课程 A 的任务"},
    )

    response = await client.post(
        "/api/v1/study-logs",
        headers=headers,
        json={
            "course_id": second_course.json()["id"],
            "task_id": task.json()["id"],
            "minutes": 30,
        },
    )
    assert response.status_code == 400


async def test_deleting_course_cascades(client: AsyncClient) -> None:
    headers = await register_and_login(client)
    course = await client.post(
        "/api/v1/courses",
        headers=headers,
        json={"name": "临时项目"},
    )
    course_id = course.json()["id"]
    await client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"course_id": course_id, "title": "临时任务"},
    )
    await client.post(
        "/api/v1/study-logs",
        headers=headers,
        json={"course_id": course_id, "minutes": 10},
    )

    deleted = await client.delete(f"/api/v1/courses/{course_id}", headers=headers)
    assert deleted.status_code == 204

    tasks = await client.get("/api/v1/tasks", headers=headers)
    logs = await client.get("/api/v1/study-logs", headers=headers)
    assert tasks.json()["total"] == 0
    assert logs.json()["total"] == 0