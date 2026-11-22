from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseList, CourseRead, CourseUpdate
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["学习项目"])


@router.get("", response_model=CourseList)
async def list_courses(
    include_archived: bool = Query(False, description="是否包含已归档项目"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseList:
    courses = await course_service.list_courses(db, current_user.id, include_archived)
    return CourseList(items=courses, total=len(courses))


@router.post("", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Course:
    return await course_service.create_course(db, current_user.id, data)


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Course:
    return await course_service.get_owned_course(db, course_id, current_user.id)


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Course:
    course = await course_service.get_owned_course(db, course_id, current_user.id)
    return await course_service.update_course(db, course, data)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    course = await course_service.get_owned_course(db, course_id, current_user.id)
    await course_service.delete_course(db, course)
    return Response(status_code=status.HTTP_204_NO_CONTENT)