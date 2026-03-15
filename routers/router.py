from fastapi import APIRouter
from routers import users, incidents

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users.router)
api_router.include_router(incidents.router)
# api_router.include_router(notifications.router)
# api_router.include_router(tasks.router)