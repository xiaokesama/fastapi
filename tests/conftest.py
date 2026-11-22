from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Course, StudyLog, Task, User  # noqa: F401


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_engine) -> AsyncIterator[AsyncClient]:
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client
    app.dependency_overrides.clear()


async def register_and_login(
    client: AsyncClient,
    username: str = "learner",
    email: str = "learner@example.com",
    password: str = "password123",
) -> dict[str, str]:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert register_response.status_code == 201, register_response.text

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}