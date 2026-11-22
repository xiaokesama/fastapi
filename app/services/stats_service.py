from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.enums import TaskStatus
from app.models.study_log import StudyLog
from app.models.task import Task
from app.schemas.stats import CourseStats, DailyMinutes, OverviewStats


async def get_overview(db: AsyncSession, user_id: int, days: int = 14) -> OverviewStats:
    rows = (
        await db.execute(
            select(StudyLog.studied_on, func.sum(StudyLog.minutes))
            .where(StudyLog.user_id == user_id)
            .group_by(StudyLog.studied_on)
        )
    ).all()
    minutes_by_day = {row[0]: int(row[1] or 0) for row in rows}

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    total_minutes = sum(minutes_by_day.values())
    today_minutes = minutes_by_day.get(today, 0)
    week_minutes = sum(value for day, value in minutes_by_day.items() if day >= week_start)

    streak = 0
    cursor = today
    if minutes_by_day.get(cursor, 0) == 0:
        cursor -= timedelta(days=1)
    while minutes_by_day.get(cursor, 0) > 0:
        streak += 1
        cursor -= timedelta(days=1)

    task_counts = (
        await db.execute(
            select(Task.status, func.count(Task.id))
            .join(Course, Task.course_id == Course.id)
            .where(Course.owner_id == user_id)
            .group_by(Task.status)
        )
    ).all()
    task_count_by_status = {row[0]: int(row[1]) for row in task_counts}

    active_courses = await db.scalar(
        select(func.count(Course.id)).where(
            Course.owner_id == user_id,
            Course.is_archived.is_(False),
        )
    )

    start_day = today - timedelta(days=days - 1)
    daily_minutes = [
        DailyMinutes(date=day, minutes=minutes_by_day.get(day, 0))
        for day in (start_day + timedelta(days=offset) for offset in range(days))
    ]

    return OverviewStats(
        total_minutes=total_minutes,
        today_minutes=today_minutes,
        week_minutes=week_minutes,
        current_streak=streak,
        total_tasks=sum(task_count_by_status.values()),
        completed_tasks=task_count_by_status.get(TaskStatus.done, 0),
        active_courses=int(active_courses or 0),
        daily_minutes=daily_minutes,
    )


async def get_course_stats(db: AsyncSession, user_id: int) -> list[CourseStats]:
    courses = list(
        (
            await db.scalars(
                select(Course)
                .where(Course.owner_id == user_id, Course.is_archived.is_(False))
                .order_by(Course.created_at.asc())
            )
        ).all()
    )
    if not courses:
        return []

    log_rows = (
        await db.execute(
            select(StudyLog.course_id, func.sum(StudyLog.minutes))
            .where(StudyLog.user_id == user_id)
            .group_by(StudyLog.course_id)
        )
    ).all()
    minutes_by_course = {row[0]: int(row[1] or 0) for row in log_rows}

    task_rows = (
        await db.execute(
            select(Task.course_id, Task.status, func.count(Task.id))
            .join(Course, Task.course_id == Course.id)
            .where(Course.owner_id == user_id)
            .group_by(Task.course_id, Task.status)
        )
    ).all()
    task_counts: dict[int, dict[TaskStatus, int]] = defaultdict(lambda: defaultdict(int))
    for course_id, status, count in task_rows:
        task_counts[course_id][status] = int(count)

    result: list[CourseStats] = []
    for course in courses:
        counts = task_counts[course.id]
        result.append(
            CourseStats(
                course_id=course.id,
                course_name=course.name,
                minutes=minutes_by_course.get(course.id, 0),
                completed_tasks=counts.get(TaskStatus.done, 0),
                total_tasks=sum(counts.values()),
            )
        )
    return result