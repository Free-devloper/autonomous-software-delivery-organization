"""Audit-event hashing and persistence helpers."""

from __future__ import annotations

import hashlib
import json
from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol, cast
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditEvent, AuditOutcome


class TenantSessionFactory(Protocol):
    def transaction(self, organization_id: UUID) -> AbstractAsyncContextManager[AsyncSession]: ...


def _canonical_json(data: dict[str, object]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class AuditEventRepository:
    async def get_latest_event_hash(
        self, session: AsyncSession, organization_id: UUID
    ) -> str | None:
        statement: Select[tuple[str]] = (
            select(AuditEvent.event_hash)
            .where(AuditEvent.organization_id == organization_id)
            .order_by(AuditEvent.sequence_id.desc())
            .limit(1)
        )
        return cast(str | None, await session.scalar(statement))

    async def add(self, session: AsyncSession, event: AuditEvent) -> AuditEvent:
        session.add(event)
        await session.flush()
        return event


class AuditEventService:
    def __init__(
        self,
        session_factory: TenantSessionFactory,
        repository: AuditEventRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or AuditEventRepository()

    async def record(
        self,
        *,
        organization_id: UUID,
        actor_id: str,
        action: str,
        resource_type: str,
        outcome: AuditOutcome,
        resource_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event_context: dict[str, object] = dict(context or {})
        async with self._session_factory.transaction(organization_id) as session:
            previous_hash = await self._repository.get_latest_event_hash(session, organization_id)
            payload: dict[str, object] = {
                "organization_id": str(organization_id),
                "actor_id": actor_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "outcome": outcome,
                "context": event_context,
                "previous_event_hash": previous_hash,
            }
            payload_hash = _sha256_hex(_canonical_json(payload))
            event_hash = _sha256_hex(
                _canonical_json({"payload_hash": payload_hash, "previous": previous_hash})
            )
            return await self._repository.add(
                session,
                AuditEvent(
                    organization_id=organization_id,
                    actor_id=actor_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    outcome=outcome,
                    context=event_context,
                    previous_event_hash=previous_hash,
                    payload_hash=payload_hash,
                    event_hash=event_hash,
                ),
            )
