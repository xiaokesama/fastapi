from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("项目名称不能为空")
        return value


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    is_archived: bool | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("项目名称不能为空")
        return value


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    color: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class CourseList(BaseModel):
    items: list[CourseRead]
    total: int