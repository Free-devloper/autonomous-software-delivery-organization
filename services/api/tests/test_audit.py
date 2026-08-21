from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from autonomous_sdo_api.database.audit import AuditEventRepository, AuditEventService
from autonomous_sdo_api.database.models import AuditEvent

pytestmark = pytest.mark.unit


class _MemorySessionFactory:
    def __init__(self) -> None:
        self.organization_scopes: list[UUID] = []
        self.session = cast(AsyncSession, object())

    @asynccontextmanager
    async def transaction(self, organization_id: UUID) -> AsyncIterator[AsyncSession]:
        self.organization_scopes.append(organization_id)
        yield self.session


class _MemoryAuditRepository(AuditEventRepository):
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def get_latest_event_hash(
        self, session: AsyncSession, organization_id: UUID
    ) -> str | None:
        for event in reversed(self.events):
            if event.organization_id == organization_id:
                return event.event_hash
        return None

    async def add(self, session: AsyncSession, event: AuditEvent) -> AuditEvent:
        self.events.append(event)
        return event


async def _record_event(
    *,
    organization_id: UUID,
    context: dict[str, object],
) -> tuple[AuditEvent, _MemorySessionFactory, _MemoryAuditRepository]:
    session_factory = _MemorySessionFactory()
    repository = _MemoryAuditRepository()
    service = AuditEventService(session_factory, repository)

    event = await service.record(
        organization_id=organization_id,
        actor_id="actor-one",
        action="organization.configuration.read",
        resource_type="organization_configuration",
        outcome="success",
        context=context,
    )
    return event, session_factory, repository


def test_audit_event_service_records_canonical_hashes_in_tenant_scope() -> None:
    organization_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")

    event, session_factory, repository = asyncio.run(
        _record_event(
            organization_id=organization_id,
            context={"b": 2, "a": 1},
        )
    )
    duplicate, _, _ = asyncio.run(
        _record_event(
            organization_id=organization_id,
            context={"a": 1, "b": 2},
        )
    )

    assert session_factory.organization_scopes == [organization_id]
    assert repository.events == [event]
    assert event.organization_id == organization_id
    assert event.previous_event_hash is None
    assert len(event.payload_hash) == 64
    assert len(event.event_hash) == 64
    assert duplicate.payload_hash == event.payload_hash
    assert duplicate.event_hash == event.event_hash


def test_audit_event_service_chains_events_per_organization() -> None:
    organization_one_id = UUID("018f4b9d-4c5d-7abc-8def-0123456789ab")
    organization_two_id = UUID("018f4b9d-4c5d-7abc-8def-111111111111")
    session_factory = _MemorySessionFactory()
    repository = _MemoryAuditRepository()
    service = AuditEventService(session_factory, repository)

    async def scenario() -> tuple[AuditEvent, AuditEvent, AuditEvent]:
        first = await service.record(
            organization_id=organization_one_id,
            actor_id="actor-one",
            action="organization.configuration.read",
            resource_type="organization_configuration",
            outcome="success",
        )
        second = await service.record(
            organization_id=organization_one_id,
            actor_id="actor-one",
            action="organization.configuration.read",
            resource_type="organization_configuration",
            outcome="success",
        )
        other_tenant = await service.record(
            organization_id=organization_two_id,
            actor_id="actor-two",
            action="organization.configuration.read",
            resource_type="organization_configuration",
            outcome="success",
        )
        return first, second, other_tenant

    first, second, other_tenant = asyncio.run(scenario())

    assert second.previous_event_hash == first.event_hash
    assert other_tenant.previous_event_hash is None
    assert session_factory.organization_scopes == [
        organization_one_id,
        organization_one_id,
        organization_two_id,
    ]
