from fastapi import APIRouter
from routers import users, incidents, tasks,notifications,ws_notification,teams

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(users.router)
api_router.include_router(incidents.router)
api_router.include_router(tasks.router)
api_router.include_router(notifications.router)
api_router.include_router(ws_notification.router)
api_router.include_router(teams.router)