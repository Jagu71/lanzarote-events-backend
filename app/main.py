from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging


settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    description=(
        "Backend para un agregador de eventos culturales y de ocio "
        "de Lanzarote con scraping modular y soporte multiidioma."
    ),
)
app.include_router(api_router, prefix=settings.api_v1_prefix)
frontend_dir = settings.base_dir / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def frontend_index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/admin", include_in_schema=False)
def admin_index() -> FileResponse:
    return FileResponse(frontend_dir / "admin.html")
