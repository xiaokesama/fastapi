from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    return await auth_service.create_user(db, data)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(
        access_token=create_access_token(str(user.id)),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user