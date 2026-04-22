from fastapi import APIRouter

from app.api.routes_admin_sources import router as admin_sources_router
from app.api.routes_categories import router as categories_router
from app.api.routes_events import router as events_router


api_router = APIRouter()
api_router.include_router(events_router)
api_router.include_router(categories_router)
api_router.include_router(admin_sources_router)
