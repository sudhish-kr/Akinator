from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.db.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Alembic uses a sync driver. Strip SQLite async; for Postgres prefer psycopg2
# when present, otherwise SQLAlchemy's psycopg (v3) dialect.
def _sync_database_url(url: str) -> str:
    if "+aiosqlite" in url:
        return url.replace("+aiosqlite", "")
    if "+asyncpg" not in url:
        return url
    psycopg2_url = url.replace("+asyncpg", "")
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        return url.replace("+asyncpg", "+psycopg")
    return psycopg2_url


sync_url = _sync_database_url(settings.database_url)
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
