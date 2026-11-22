from fastapi import APIRouter

from app.api.routes import auth, courses, stats, study_logs, tasks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(tasks.router)
api_router.include_router(study_logs.router)
api_router.include_router(stats.router)