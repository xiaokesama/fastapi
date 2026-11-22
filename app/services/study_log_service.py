from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.study_log import StudyLog
from app.schemas.study_log import StudyLogCreate
from app.services import course_service, task_service


async def create_study_log(
    db: AsyncSession,
    user_id: int,
    data: StudyLogCreate,
) -> StudyLog:
    await course_service.get_owned_course(db, data.course_id, user_id)

    if data.task_id is not None:
        task = await task_service.get_owned_task(db, data.task_id, user_id)
        if task.course_id != data.course_id:
            raise BadRequestError("任务不属于所选学习项目")

    study_log = StudyLog(user_id=user_id, **data.model_dump())
    db.add(study_log)
    await db.commit()
    await db.refresh(study_log)
    return study_log


async def list_study_logs(
    db: AsyncSession,
    user_id: int,
    *,
    course_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[StudyLog], int]:
    if start_date and end_date and start_date > end_date:
        raise BadRequestError("开始日期不能晚于结束日期")

    filters = [StudyLog.user_id == user_id]
    if course_id is not None:
        filters.append(StudyLog.course_id == course_id)
    if start_date is not None:
        filters.append(StudyLog.studied_on >= start_date)
    if end_date is not None:
        filters.append(StudyLog.studied_on <= end_date)

    base_statement = select(StudyLog).where(*filters)
    count_statement = select(func.count()).select_from(base_statement.subquery())
    total = await db.scalar(count_statement) or 0

    statement = (
        base_statement.order_by(StudyLog.studied_on.desc(), StudyLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.scalars(statement)
    return list(result.all()), total


async def get_owned_study_log(db: AsyncSession, log_id: int, user_id: int) -> StudyLog:
    statement = select(StudyLog).where(StudyLog.id == log_id, StudyLog.user_id == user_id)
    study_log = await db.scalar(statement)
    if study_log is None:
        raise NotFoundError("学习记录不存在")
    return study_log


async def delete_study_log(db: AsyncSession, study_log: StudyLog) -> None:
    await db.delete(study_log)
    await db.commit()