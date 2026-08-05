"""Background jobs — session cleanup per TDD Section 7."""

import asyncio
import logging

from app.config import settings
from app.db.repositories.game_repository import GameRepository
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)


async def abandon_stale_sessions_once() -> int:
    async with async_session_factory() as db:
        repo = GameRepository(db)
        count = await repo.abandon_stale_sessions(settings.session_abandon_minutes)
        await repo.commit()
        if count:
            logger.info("Abandoned %d stale sessions", count)
        return count


async def run_session_cleanup_loop(interval_seconds: int = 300) -> None:
    """Mark inactive sessions as abandoned every 5 minutes."""
    while True:
        try:
            await abandon_stale_sessions_once()
        except Exception:
            logger.exception("Session cleanup job failed")
        await asyncio.sleep(interval_seconds)
