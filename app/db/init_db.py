from app.db.base import Base
from app.db.session import engine

# Importing models registers their tables on Base.metadata.
from app.models import Course, StudyLog, Task, User  # noqa: F401


async def init_db() -> None:
    """Create tables when the application starts.

    This is convenient for local learning. In a production project, replace it
    with Alembic migrations and set AUTO_CREATE_TABLES=false.
    """
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)