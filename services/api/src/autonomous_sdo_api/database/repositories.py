"""Persistence-only repositories with tenant predicates as defense in depth."""

from __future__ import annotations

from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import OrganizationConfiguration


class OrganizationConfigurationRepository:
    async def get_for_organization(
        self, session: AsyncSession, organization_id: UUID
    ) -> OrganizationConfiguration | None:
        statement = select(OrganizationConfiguration).where(
            OrganizationConfiguration.organization_id == organization_id
        )
        return cast(OrganizationConfiguration | None, await session.scalar(statement))
