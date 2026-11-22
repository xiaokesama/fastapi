from datetime import date

from pydantic import BaseModel


class DailyMinutes(BaseModel):
    date: date
    minutes: int


class OverviewStats(BaseModel):
    total_minutes: int
    today_minutes: int
    week_minutes: int
    current_streak: int
    total_tasks: int
    completed_tasks: int
    active_courses: int
    daily_minutes: list[DailyMinutes]


class CourseStats(BaseModel):
    course_id: int
    course_name: str
    minutes: int
    completed_tasks: int
    total_tasks: int