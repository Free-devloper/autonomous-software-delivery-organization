"""Async PostgreSQL session handling with transaction-local RLS context."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_SET_ORGANIZATION_CONTEXT: Final = text(
    "SELECT set_config('asdo.organization_id', :organization_id, true)"
)


class TenantScopedSessionFactory:
    """Open transactions constrained by PostgreSQL RLS and own their engine lifecycle."""

    def __init__(
        self, engine_or_session_factory: AsyncEngine | async_sessionmaker[AsyncSession]
    ) -> None:
        """Build production sessions from an engine or accept a test session factory."""
        if isinstance(engine_or_session_factory, AsyncEngine):
            self._engine: AsyncEngine | None = engine_or_session_factory
            self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)
        else:
            self._engine = None
            self._session_factory = engine_or_session_factory

    @asynccontextmanager
    async def transaction(self, organization_id: UUID) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            async with session.begin():
                await session.execute(
                    _SET_ORGANIZATION_CONTEXT, {"organization_id": str(organization_id)}
                )
                yield session

    async def ping(self) -> None:
        """Verify that a database connection can execute a bounded trivial query."""
        async with self._session_factory() as session:
            await session.execute(text("SELECT 1"))

    async def close(self) -> None:
        """Dispose the production engine and return all pooled connections."""
        if self._engine is not None:
            await self._engine.dispose()


def create_tenant_session_factory(database_url: str) -> TenantScopedSessionFactory:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    return TenantScopedSessionFactory(engine)
