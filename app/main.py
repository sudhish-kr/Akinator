import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.game import router as game_router
from app.config import settings
from app.core.logging import request_logging_middleware, setup_logging
from app.db.session import async_session_factory
from app.services.media_service import media_root
from app.workers.monitoring import get_worker_status

setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Session cleanup runs on Celery beat (abandon_stale_sessions).
    # Keep a lightweight in-process fallback only when workers run eager/local.
    cleanup_task = None
    if settings.celery_task_always_eager:
        from app.workers.session_cleanup import run_session_cleanup_loop

        cleanup_task = asyncio.create_task(run_session_cleanup_loop())
    yield
    if cleanup_task is not None:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(request_logging_middleware)

app.include_router(auth_router)
app.include_router(game_router)
app.include_router(admin_router)

app.mount("/media", StaticFiles(directory=str(media_root())), name="media")


@app.get("/health", tags=["health"])
async def health():
    """Liveness probe."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/health/ready", tags=["health"])
async def readiness():
    """Readiness probe — verifies database connectivity."""
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception:
        from fastapi import Response

        return Response(
            content='{"status": "not_ready", "database": "unreachable"}',
            status_code=503,
            media_type="application/json",
        )


@app.get("/health/workers", tags=["health"])
async def workers_health():
    """Celery worker / queue monitoring endpoint."""
    return get_worker_status()
