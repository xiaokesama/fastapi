from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_\-\u4e00-\u9fff]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime