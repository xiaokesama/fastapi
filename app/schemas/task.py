from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    due_date: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=10080)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("任务标题不能为空")
        return value


class TaskUpdate(BaseModel):
    course_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=10080)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("任务标题不能为空")
        return value


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    estimated_minutes: int | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskList(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int
    has_next: bool