import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.game import router as game_router
from app.config import settings
from app.core.logging import request_logging_middleware, setup_logging
from app.db.session import async_session_factory
from app.workers.session_cleanup import run_session_cleanup_loop

setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(run_session_cleanup_loop())
    yield
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

# Register logging first, then CORS last so CORS is outermost and still
# attaches headers when routes return error Responses (e.g. DB failures).
app.middleware("http")(request_logging_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(game_router)
app.include_router(admin_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return JSON 500 with CORS headers so the browser does not report Failed to fetch."""
    headers = {
        "Access-Control-Allow-Origin": request.headers.get("origin")
        or settings.cors_origin_list[0],
        "Access-Control-Allow-Credentials": "true",
        "Vary": "Origin",
    }
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origin_list:
        headers.pop("Access-Control-Allow-Origin", None)
        headers.pop("Access-Control-Allow-Credentials", None)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers=headers,
    )


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
