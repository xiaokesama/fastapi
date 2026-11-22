from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    courses: Mapped[list["Course"]] = relationship(  # noqa: F821
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    study_logs: Mapped[list["StudyLog"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )