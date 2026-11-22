from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskList, TaskRead, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["学习任务"])


@router.get("", response_model=TaskList)
async def list_tasks(
    course_id: int | None = Query(None, description="按学习项目筛选"),
    task_status: TaskStatus | None = Query(None, alias="status", description="按状态筛选"),
    priority: TaskPriority | None = Query(None, description="按优先级筛选"),
    search: str | None = Query(None, max_length=100, description="搜索标题"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskList:
    items, total = await task_service.list_tasks(
        db,
        current_user.id,
        course_id=course_id,
        status=task_status,
        priority=priority,
        search=search,
        page=page,
        page_size=page_size,
    )
    return TaskList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    return await task_service.create_task(db, current_user.id, data)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    return await task_service.get_owned_task(db, task_id, current_user.id)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = await task_service.get_owned_task(db, task_id, current_user.id)
    return await task_service.update_task(db, task, data, current_user.id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    task = await task_service.get_owned_task(db, task_id, current_user.id)
    await task_service.delete_task(db, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)