from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_login(db: AsyncSession, login: str) -> User | None:
    normalized = login.strip().lower()
    statement = select(User).where(
        or_(
            func.lower(User.username) == normalized,
            func.lower(User.email) == normalized,
        )
    )
    return await db.scalar(statement)


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.scalar(
        select(User).where(
            or_(
                func.lower(User.username) == data.username.lower(),
                func.lower(User.email) == data.email.lower(),
            )
        )
    )
    if existing is not None:
        raise ConflictError("用户名或邮箱已被注册")

    user = User(
        username=data.username,
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, login: str, password: str) -> User | None:
    user = await get_user_by_login(db, login)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user