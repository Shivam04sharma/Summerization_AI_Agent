"""Async PostgreSQL connection pool using asyncpg."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

import asyncpg
import structlog
from config import settings
from redis.asyncio import Redis

logger = structlog.get_logger()

_pool: asyncpg.Pool | None = None

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def init_db() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=settings.db_dsn,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
    )
    await _run_migrations()
    logger.info("db_initialized", dsn=settings.db_dsn.split("@")[-1], schema=settings.db_schema)


async def close_db() -> None:
    if _pool:
        await _pool.close()
        logger.info("db_pool_closed")


def get_pool() -> asyncpg.Pool:
    return _pool


async def get_redis() -> AsyncGenerator[Redis, None]:
    """FastAPI dependency — yields a Redis client."""
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def _run_migrations() -> None:
    """
    Runs pending SQL migrations in version order.
    Tracking table: {db_schema}.schema_migrations
    SQL files: db/migrations/local/V{n}__{description}.sql
    """
    schema = settings.db_schema
    if not schema:
        logger.warning("db_schema_not_configured", msg="DB_SCHEMA is empty, skipping migrations")
        return

    env = settings.env.lower()
    migration_dir = _MIGRATIONS_DIR / env

    if not migration_dir.exists():
        logger.warning("migrations_dir_not_found", path=str(migration_dir))
        return

    sql_files = sorted(
        migration_dir.glob("V*.sql"),
        key=lambda f: int(f.stem.split("__")[0].lstrip("V")),
    )

    if not sql_files:
        logger.info("no_migrations_found", env=env)
        return

    async with _pool.acquire() as conn:  # type: ignore[union-attr]
        # Create schema + tracking table — schema name from settings
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.schema_migrations (
                version     VARCHAR(100) PRIMARY KEY,
                applied_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            );
        """)

        for sql_file in sql_files:
            version = sql_file.stem
            already_applied = await conn.fetchval(
                f"SELECT 1 FROM {schema}.schema_migrations WHERE version = $1", version
            )
            if already_applied:
                logger.info("migration_skipped", version=version)
                continue

            # Inject schema name into SQL file content
            sql = sql_file.read_text(encoding="utf-8").replace("{schema}", schema)
            await conn.execute(sql)
            await conn.execute(
                f"INSERT INTO {schema}.schema_migrations (version) VALUES ($1)", version
            )
            logger.info("migration_applied", version=version, env=env, schema=schema)
