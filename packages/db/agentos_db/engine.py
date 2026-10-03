"""Async SQLAlchemy engine. Postgres (compose) is the target; SQLite (aiosqlite) is allowed
for dev/tests via AGENTOS_DB_URL so the skeleton is runnable without the full stack — the
engine flag never changes schema or semantics, only the driver."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from agentos_contracts.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = get_settings().db_url
        kwargs = {}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"timeout": 30}
        _engine = create_async_engine(url, pool_pre_ping=True, **kwargs)
    return _engine


def get_sessionmaker() -> async_sessionmaker:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def ensure_schema() -> None:
    from agentos_db.orm import Base

    eng = get_engine()

    def _create(sync_conn):
        Base.metadata.create_all(sync_conn)

    async with eng.begin() as conn:
        await conn.run_sync(_create)


async def close_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
