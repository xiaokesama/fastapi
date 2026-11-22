from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Course(TimestampMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#6366f1", nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    owner: Mapped["User"] = relationship(back_populates="courses")  # noqa: F821
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    study_logs: Mapped[list["StudyLog"]] = relationship(  # noqa: F821
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )