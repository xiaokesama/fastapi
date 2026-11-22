from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.course import Course
from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import course_service


async def get_owned_task(db: AsyncSession, task_id: int, user_id: int) -> Task:
    statement = (
        select(Task)
        .join(Course, Task.course_id == Course.id)
        .where(Task.id == task_id, Course.owner_id == user_id)
    )
    task = await db.scalar(statement)
    if task is None:
        raise NotFoundError("学习任务不存在")
    return task


async def list_tasks(
    db: AsyncSession,
    user_id: int,
    *,
    course_id: int | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Task], int]:
    filters = [Course.owner_id == user_id]
    if course_id is not None:
        filters.append(Task.course_id == course_id)
    if status is not None:
        filters.append(Task.status == status)
    if priority is not None:
        filters.append(Task.priority == priority)
    if search:
        filters.append(Task.title.ilike(f"%{search.strip()}%"))

    base_statement = select(Task).join(Course, Task.course_id == Course.id).where(*filters)
    count_statement = select(func.count()).select_from(base_statement.subquery())
    total = await db.scalar(count_statement) or 0

    statement = (
        base_statement.order_by(Task.status.asc(), Task.due_date.asc(), Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.scalars(statement)
    return list(result.all()), total


async def create_task(db: AsyncSession, user_id: int, data: TaskCreate) -> Task:
    await course_service.get_owned_course(db, data.course_id, user_id)
    payload = data.model_dump()
    if payload["status"] == TaskStatus.done:
        payload["completed_at"] = datetime.now(UTC)
    task = Task(**payload)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    task: Task,
    data: TaskUpdate,
    user_id: int,
) -> Task:
    updates = data.model_dump(exclude_unset=True)
    for field in ("course_id", "title", "status", "priority"):
        if field in updates and updates[field] is None:
            raise BadRequestError(f"{field} 不能为 null")

    if "course_id" in updates:
        await course_service.get_owned_course(db, updates["course_id"], user_id)

    if "status" in updates:
        if updates["status"] == TaskStatus.done and task.status != TaskStatus.done:
            updates["completed_at"] = datetime.now(UTC)
        elif updates["status"] != TaskStatus.done:
            updates["completed_at"] = None

    for field, value in updates.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


async def set_task_status(
    db: AsyncSession,
    task: Task,
    status: TaskStatus,
    user_id: int,
) -> Task:
    data = TaskUpdate(status=status)
    return await update_task(db, task, data, user_id)


async def delete_task(db: AsyncSession, task: Task) -> None:
    await db.delete(task)
    await db.commit()