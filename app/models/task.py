from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TaskPriority, TaskStatus
from app.models.mixins import TimestampMixin


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=20),
        default=TaskStatus.todo,
        index=True,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, native_enum=False, length=20),
        default=TaskPriority.medium,
        index=True,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    course: Mapped["Course"] = relationship(back_populates="tasks")  # noqa: F821
    study_logs: Mapped[list["StudyLog"]] = relationship(  # noqa: F821
        back_populates="task",
        passive_deletes=True,
    )