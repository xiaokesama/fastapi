from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.study_log import StudyLog
from app.models.user import User
from app.schemas.study_log import StudyLogCreate, StudyLogList, StudyLogRead
from app.services import study_log_service

router = APIRouter(prefix="/study-logs", tags=["学习记录"])


@router.get("", response_model=StudyLogList)
async def list_study_logs(
    course_id: int | None = Query(None, description="按学习项目筛选"),
    start_date: date | None = Query(None, description="开始日期"),
    end_date: date | None = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudyLogList:
    items, total = await study_log_service.list_study_logs(
        db,
        current_user.id,
        course_id=course_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return StudyLogList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=page * page_size < total,
    )


@router.post("", response_model=StudyLogRead, status_code=status.HTTP_201_CREATED)
async def create_study_log(
    data: StudyLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudyLog:
    return await study_log_service.create_study_log(db, current_user.id, data)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    study_log = await study_log_service.get_owned_study_log(db, log_id, current_user.id)
    await study_log_service.delete_study_log(db, study_log)
    return Response(status_code=status.HTTP_204_NO_CONTENT)