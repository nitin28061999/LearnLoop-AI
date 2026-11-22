from fastapi import FastAPI  # pyright: ignore[reportMissingImports]

from app.api.routes.health import router as health_router
from app.api.routes.learning import router as learning_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Adaptive Learning Intelligence Platform",
    version=settings.app_version,
    debug=settings.debug,
)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(learning_router, prefix=settings.api_v1_prefix)
