from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.url import normalize_asyncpg_url

_engine_url, _connect_args = normalize_asyncpg_url(settings.database_url)

_engine_kwargs: dict = {
    "echo": settings.debug,
    "connect_args": _connect_args,
}
if not _engine_url.startswith("sqlite"):
    # Render/Neon: keep the pool tiny so catalog load + requests don't
    # multiply connection RSS / Neon connection-slot use.
    _engine_kwargs.update(
        pool_size=2,
        max_overflow=1,
        pool_pre_ping=True,
        pool_recycle=300,
    )

engine = create_async_engine(_engine_url, **_engine_kwargs)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

if _engine_url.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _sqlite_on_connect(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA cache_size=-65536")
        cursor.close()


async def get_db():
    async with async_session_factory() as session:
        yield session
