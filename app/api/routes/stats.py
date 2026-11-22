from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.stats import CourseStats, OverviewStats
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["学习统计"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview(
    days: int = Query(14, ge=1, le=90, description="每日趋势包含的天数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OverviewStats:
    return await stats_service.get_overview(db, current_user.id, days)


@router.get("/courses", response_model=list[CourseStats])
async def get_course_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CourseStats]:
    return await stats_service.get_course_stats(db, current_user.id)