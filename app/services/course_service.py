from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate


async def list_courses(
    db: AsyncSession,
    user_id: int,
    include_archived: bool = False,
) -> list[Course]:
    statement = select(Course).where(Course.owner_id == user_id)
    if not include_archived:
        statement = statement.where(Course.is_archived.is_(False))
    statement = statement.order_by(Course.is_archived.asc(), Course.created_at.desc())
    result = await db.scalars(statement)
    return list(result.all())


async def get_owned_course(db: AsyncSession, course_id: int, user_id: int) -> Course:
    statement = select(Course).where(Course.id == course_id, Course.owner_id == user_id)
    course = await db.scalar(statement)
    if course is None:
        raise NotFoundError("学习项目不存在")
    return course


async def create_course(db: AsyncSession, user_id: int, data: CourseCreate) -> Course:
    course = Course(owner_id=user_id, **data.model_dump())
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def update_course(
    db: AsyncSession,
    course: Course,
    data: CourseUpdate,
) -> Course:
    updates = data.model_dump(exclude_unset=True)
    for field in ("name", "color", "is_archived"):
        if field in updates and updates[field] is None:
            raise BadRequestError(f"{field} 不能为 null")

    for field, value in updates.items():
        setattr(course, field, value)

    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course: Course) -> None:
    await db.delete(course)
    await db.commit()