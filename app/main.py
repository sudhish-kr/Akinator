import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.game import router as game_router
from app.config import settings
from app.core.logging import request_logging_middleware, setup_logging
from app.db.session import async_session_factory, engine
from app.monitoring.db import instrument_engine
from app.monitoring.health import build_health_report, check_database
from app.monitoring.metrics import APP_INFO, render_prometheus_metrics
from app.monitoring.middleware import monitoring_middleware
from app.security.middleware import RateLimitMiddleware
from app.services.media_service import media_root
from app.workers.monitoring import get_worker_status

setup_logging(settings.log_level)
instrument_engine(engine)
APP_INFO.labels(
    app=settings.app_name,
    environment=settings.environment,
    version="0.2.0",
).set(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Never block "Application startup complete" on SQLite locks / large DDL.
    migrate_task = asyncio.create_task(asyncio.to_thread(_run_migrations_safe))
    warm_task = asyncio.create_task(_warm_playable_catalog())

    # Session cleanup runs on Celery beat (abandon_stale_sessions).
    # Keep a lightweight in-process fallback only when workers run eager/local.
    cleanup_task = None
    if settings.celery_task_always_eager:
        from app.workers.session_cleanup import run_session_cleanup_loop

        cleanup_task = asyncio.create_task(run_session_cleanup_loop())
    yield
    for task in (migrate_task, warm_task, cleanup_task):
        if task is None:
            continue
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def _run_migrations_safe() -> None:
    try:
        from app.db.migrate import run_pending_migrations

        run_pending_migrations()
    except Exception:
        # Local SQLite lock / already-migrated races — app can still serve.
        pass


async def _warm_playable_catalog() -> None:
    try:
        from app.db.repositories.game_repository import GameRepository
        from app.services.playable_catalog import get_playable_catalog

        async with async_session_factory() as db:
            await get_playable_catalog(GameRepository(db))
    except Exception:
        # Empty DB / first boot — catalog loads lazily on first game start.
        pass


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    lifespan=lifespan,
)

# Register logging first, then CORS last so CORS is outermost and still
# attaches headers when routes return error Responses (e.g. DB failures).
app.middleware("http")(request_logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting wraps the app early; monitoring still records 429s as 4xx.
app.add_middleware(RateLimitMiddleware)
app.middleware("http")(monitoring_middleware)

app.include_router(auth_router)
app.include_router(game_router)
app.include_router(admin_router)

app.mount("/media", StaticFiles(directory=str(media_root())), name="media")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return JSON 500 with CORS headers so the browser does not report Failed to fetch."""
    origin = request.headers.get("origin")
    headers = {"Vary": "Origin"}
    if origin and settings.is_cors_origin_allowed(origin):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    elif not origin and settings.cors_origin_list:
        headers["Access-Control-Allow-Origin"] = settings.cors_origin_list[0]
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers=headers,
    )


@app.get("/health", tags=["health"])
async def health():
    """Liveness / aggregated health (database latency included)."""
    return await build_health_report(include_workers=True)


@app.get("/health/ready", tags=["health"])
async def readiness():
    """Readiness probe — verifies database connectivity and latency."""
    db = await check_database()
    if db["status"] != "ok":
        return Response(
            content='{"status":"not_ready","database":"unreachable"}',
            status_code=503,
            media_type="application/json",
        )
    return {
        "status": "ready",
        "database": "ok",
        "database_latency_seconds": db["latency_seconds"],
    }


@app.get("/health/workers", tags=["health"])
async def workers_health():
    """Celery worker / queue monitoring endpoint."""
    return get_worker_status()


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus-compatible metrics scrape endpoint."""
    body, content_type = render_prometheus_metrics()
    return Response(content=body, media_type=content_type)
