from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import utc_now


class StudyLog(Base):
    __tablename__ = "study_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    studied_on: Mapped[date] = mapped_column(Date, default=date.today, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="study_logs")  # noqa: F821
    course: Mapped["Course"] = relationship(back_populates="study_logs")  # noqa: F821
    task: Mapped["Task | None"] = relationship(back_populates="study_logs")  # noqa: F821