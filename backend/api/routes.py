from fastapi import APIRouter
from backend.api.alerts import router as alerts_router
from backend.api.dashboard import router as dashboard_router
from backend.api.reports import router as reports_router
from backend.api.settings import router as settings_router

api_router = APIRouter()

# Include routers
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
