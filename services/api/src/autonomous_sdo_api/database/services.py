"""Application services that coordinate tenant scope with repositories."""

from __future__ import annotations

from .models import OrganizationConfiguration
from .repositories import OrganizationConfigurationRepository
from .session import TenantScopedSessionFactory
from .tenancy import OrganizationContext


class OrganizationConfigurationService:
    def __init__(
        self,
        session_factory: TenantScopedSessionFactory,
        repository: OrganizationConfigurationRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository or OrganizationConfigurationRepository()

    async def get_for_context(
        self, context: OrganizationContext
    ) -> OrganizationConfiguration | None:
        async with self._session_factory.transaction(context.organization_id) as session:
            return await self._repository.get_for_organization(session, context.organization_id)
