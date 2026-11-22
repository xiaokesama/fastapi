from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StudyLogCreate(BaseModel):
    course_id: int
    task_id: int | None = None
    minutes: int = Field(ge=1, le=1440)
    note: str | None = Field(default=None, max_length=5000)
    studied_on: date = Field(default_factory=date.today)


class StudyLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    task_id: int | None
    minutes: int
    note: str | None
    studied_on: date
    created_at: datetime


class StudyLogList(BaseModel):
    items: list[StudyLogRead]
    total: int
    page: int
    page_size: int
    has_next: bool