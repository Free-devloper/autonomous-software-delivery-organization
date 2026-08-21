from __future__ import annotations

import asyncio
import os

import asyncpg  # type: ignore[import-untyped]
import pytest
from sqlalchemy import delete, text, update
from sqlalchemy.exc import DBAPIError

from autonomous_sdo_api.database.audit import AuditEventService
from autonomous_sdo_api.database.identifiers import new_uuid7
from autonomous_sdo_api.database.models import OrganizationConfiguration
from autonomous_sdo_api.database.services import OrganizationConfigurationService
from autonomous_sdo_api.database.session import create_tenant_session_factory
from autonomous_sdo_api.database.tenancy import OrganizationContext

pytestmark = pytest.mark.integration


def _asyncpg_url(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def test_postgresql_rls_enforces_crud_isolation_and_pool_context_reset() -> None:
    migrator_url = os.environ.get("ASDO_API_DATABASE_URL")
    application_url = os.environ.get("ASDO_TEST_DATABASE_URL")
    if migrator_url is None or application_url is None:
        pytest.skip("Phase 0B PostgreSQL integration URLs are not configured")

    organization_one_id = new_uuid7()
    organization_two_id = new_uuid7()
    organization_three_id = new_uuid7()

    async def scenario() -> None:
        migrator = await asyncpg.connect(_asyncpg_url(migrator_url))
        try:
            await migrator.executemany(
                "INSERT INTO organizations (id, slug) VALUES ($1, $2)",
                [
                    (organization_one_id, f"tenant-{organization_one_id.hex}"),
                    (organization_two_id, f"tenant-{organization_two_id.hex}"),
                    (organization_three_id, f"tenant-{organization_three_id.hex}"),
                ],
            )
        finally:
            await migrator.close()

        tenant_factory = create_tenant_session_factory(application_url)
        service = OrganizationConfigurationService(tenant_factory)
        audit_service = AuditEventService(tenant_factory)
        organization_one_configuration_id = new_uuid7()
        organization_two_configuration_id = new_uuid7()
        try:
            async with tenant_factory.transaction(organization_one_id) as session:
                session.add(
                    OrganizationConfiguration(
                        id=organization_one_configuration_id,
                        organization_id=organization_one_id,
                        data_region="eu-central-1",
                        data_classification="confidential",
                    )
                )
                first_backend_pid = await session.scalar(text("SELECT pg_backend_pid()"))

            async with tenant_factory.transaction(organization_two_id) as session:
                session.add(
                    OrganizationConfiguration(
                        id=organization_two_configuration_id,
                        organization_id=organization_two_id,
                        data_region="eu-west-1",
                        data_classification="restricted",
                    )
                )

            configuration_one = await service.get_for_context(
                OrganizationContext(organization_one_id)
            )
            configuration_two = await service.get_for_context(
                OrganizationContext(organization_two_id)
            )
            assert configuration_one is not None
            assert configuration_one.id == organization_one_configuration_id
            assert configuration_two is not None
            assert configuration_two.id == organization_two_configuration_id

            first_audit_event = await audit_service.record(
                organization_id=organization_one_id,
                actor_id="user-one",
                action="organization.configuration.read",
                resource_type="organization_configuration",
                outcome="success",
                context={"request_id": "request-one"},
            )
            second_audit_event = await audit_service.record(
                organization_id=organization_one_id,
                actor_id="user-one",
                action="organization.configuration.read",
                resource_type="organization_configuration",
                outcome="success",
                context={"request_id": "request-two"},
            )
            other_tenant_audit_event = await audit_service.record(
                organization_id=organization_two_id,
                actor_id="user-two",
                action="organization.configuration.read",
                resource_type="organization_configuration",
                outcome="success",
            )
            assert first_audit_event.previous_event_hash is None
            assert second_audit_event.previous_event_hash == first_audit_event.event_hash
            assert other_tenant_audit_event.previous_event_hash is None

            async with tenant_factory.transaction(organization_one_id) as session:
                second_backend_pid = await session.scalar(text("SELECT pg_backend_pid()"))
                changed_region = await session.scalar(
                    update(OrganizationConfiguration)
                    .where(OrganizationConfiguration.organization_id == organization_one_id)
                    .values(data_region="eu-north-1")
                    .returning(OrganizationConfiguration.data_region)
                )
                assert changed_region == "eu-north-1"
            assert second_backend_pid == first_backend_pid

            with pytest.raises(RuntimeError, match="force transaction rollback"):
                async with tenant_factory.transaction(organization_one_id) as session:
                    await session.execute(
                        update(OrganizationConfiguration)
                        .where(OrganizationConfiguration.organization_id == organization_one_id)
                        .values(data_region="rollback-must-not-persist")
                    )
                    raise RuntimeError("force transaction rollback")
            configuration_one = await service.get_for_context(
                OrganizationContext(organization_one_id)
            )
            assert configuration_one is not None
            assert configuration_one.data_region == "eu-north-1"

            async with tenant_factory.transaction(organization_one_id) as session:
                cross_tenant_updates = await session.scalars(
                    update(OrganizationConfiguration)
                    .where(OrganizationConfiguration.organization_id == organization_two_id)
                    .values(data_region="forbidden")
                    .returning(OrganizationConfiguration.organization_id)
                )
                assert cross_tenant_updates.all() == []
                cross_tenant_deletes = await session.scalars(
                    delete(OrganizationConfiguration)
                    .where(OrganizationConfiguration.organization_id == organization_two_id)
                    .returning(OrganizationConfiguration.organization_id)
                )
                assert cross_tenant_deletes.all() == []

            with pytest.raises(DBAPIError, match="organization configuration id is immutable"):
                async with tenant_factory.transaction(organization_one_id) as session:
                    await session.execute(
                        update(OrganizationConfiguration)
                        .where(OrganizationConfiguration.organization_id == organization_one_id)
                        .values(id=new_uuid7())
                    )
            configuration_one = await service.get_for_context(
                OrganizationContext(organization_one_id)
            )
            assert configuration_one is not None
            assert configuration_one.id == organization_one_configuration_id

            organization_three_configuration_id = new_uuid7()
            async with tenant_factory.transaction(organization_three_id) as session:
                session.add(
                    OrganizationConfiguration(
                        id=organization_three_configuration_id,
                        organization_id=organization_three_id,
                        data_region="eu-central-1",
                        data_classification="internal",
                    )
                )
            configuration_three = await service.get_for_context(
                OrganizationContext(organization_three_id)
            )
            assert configuration_three is not None
            assert configuration_three.id == organization_three_configuration_id
            async with tenant_factory.transaction(organization_three_id) as session:
                deleted_id = await session.scalar(
                    delete(OrganizationConfiguration)
                    .where(OrganizationConfiguration.organization_id == organization_three_id)
                    .returning(OrganizationConfiguration.id)
                )
                assert deleted_id == organization_three_configuration_id
            assert await service.get_for_context(OrganizationContext(organization_three_id)) is None
        finally:
            await tenant_factory.close()

        application_pool = await asyncpg.create_pool(
            _asyncpg_url(application_url), min_size=1, max_size=1
        )
        try:
            async with application_pool.acquire() as application:
                role = await application.fetchrow(
                    """
                    SELECT rolsuper, rolcreatedb, rolcreaterole, rolinherit, rolbypassrls
                    FROM pg_roles
                    WHERE rolname = current_user
                    """
                )
                assert role is not None
                assert dict(role) == {
                    "rolsuper": False,
                    "rolcreatedb": False,
                    "rolcreaterole": False,
                    "rolinherit": False,
                    "rolbypassrls": False,
                }
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    await application.fetch("SELECT id FROM organizations")
                assert (
                    await application.fetch(
                        "SELECT organization_id FROM organization_configurations"
                    )
                    == []
                )
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    async with application.transaction():
                        await application.execute("SET LOCAL row_security = off")
                        await application.fetch(
                            "SELECT organization_id FROM organization_configurations"
                        )
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    async with application.transaction():
                        await application.execute(
                            """
                            INSERT INTO organization_configurations
                                (id, organization_id, data_region, data_classification)
                            VALUES ($1, $2, $3, $4)
                            """,
                            new_uuid7(),
                            organization_three_id,
                            "eu-central-1",
                            "internal",
                        )
                async with application.transaction():
                    await application.execute(
                        "SELECT set_config('asdo.organization_id', $1, true)",
                        str(organization_one_id),
                    )
                    visible = await application.fetch(
                        "SELECT organization_id FROM organization_configurations "
                        "ORDER BY organization_id"
                    )
                    assert [record["organization_id"] for record in visible] == [
                        organization_one_id
                    ]
                    visible_audit = await application.fetch(
                        "SELECT organization_id, previous_event_hash FROM audit_events "
                        "ORDER BY sequence_id"
                    )
                    assert [record["organization_id"] for record in visible_audit] == [
                        organization_one_id,
                        organization_one_id,
                    ]
                    assert visible_audit[1]["previous_event_hash"] == first_audit_event.event_hash
                    assert (
                        await application.execute(
                            """
                            UPDATE organization_configurations
                            SET data_region = $1
                            WHERE organization_id = $2
                            """,
                            "eu-central-1",
                            organization_two_id,
                        )
                        == "UPDATE 0"
                    )
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    async with application.transaction():
                        await application.execute(
                            "SELECT set_config('asdo.organization_id', $1, true)",
                            str(organization_one_id),
                        )
                        await application.execute(
                            """
                            INSERT INTO audit_events (
                              id,
                              organization_id,
                              actor_id,
                              action,
                              resource_type,
                              outcome,
                              context,
                              payload_hash,
                              event_hash
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, '{}'::jsonb, $7, $8)
                            """,
                            new_uuid7(),
                            organization_two_id,
                            "user-one",
                            "forbidden",
                            "audit_event",
                            "denied",
                            "0" * 64,
                            "1" * 64,
                        )
                transaction = application.transaction()
                await transaction.start()
                await application.execute(
                    "SELECT set_config('asdo.organization_id', $1, true)",
                    str(organization_one_id),
                )
                await transaction.rollback()
                assert (
                    await application.fetch(
                        "SELECT organization_id FROM organization_configurations"
                    )
                    == []
                )
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    async with application.transaction():
                        await application.execute(
                            "SELECT set_config('asdo.organization_id', $1, true)",
                            str(organization_one_id),
                        )
                        await application.execute(
                            """
                            UPDATE organization_configurations
                            SET organization_id = $1
                            WHERE organization_id = $2
                            """,
                            organization_two_id,
                            organization_one_id,
                        )
                with pytest.raises(asyncpg.InsufficientPrivilegeError):
                    async with application.transaction():
                        await application.execute(
                            "SELECT set_config('asdo.organization_id', $1, true)",
                            str(organization_one_id),
                        )
                        await application.execute(
                            "UPDATE audit_events SET action = $1 WHERE organization_id = $2",
                            "tamper",
                            organization_one_id,
                        )
                async with application.transaction():
                    await application.execute(
                        "SELECT set_config('asdo.organization_id', $1, true)",
                        str(organization_one_id),
                    )
                    result = await application.execute(
                        "DELETE FROM organization_configurations WHERE organization_id = $1",
                        organization_two_id,
                    )
                    assert result == "DELETE 0"
            async with application_pool.acquire() as reused_connection:
                assert (
                    await reused_connection.fetch(
                        "SELECT organization_id FROM organization_configurations"
                    )
                    == []
                )
                assert (
                    await reused_connection.fetch("SELECT organization_id FROM audit_events") == []
                )
                with pytest.raises(asyncpg.InvalidTextRepresentationError):
                    async with reused_connection.transaction():
                        await reused_connection.execute(
                            "SELECT set_config('asdo.organization_id', 'not-a-uuid', true)"
                        )
                        await reused_connection.fetch(
                            "SELECT organization_id FROM organization_configurations"
                        )
                assert (
                    await reused_connection.fetch(
                        "SELECT organization_id FROM organization_configurations"
                    )
                    == []
                )
        finally:
            await application_pool.close()

        migrator = await asyncpg.connect(_asyncpg_url(migrator_url))
        try:
            with pytest.raises(asyncpg.CheckViolationError, match="audit events are append only"):
                await migrator.execute(
                    "UPDATE audit_events SET action = $1 WHERE organization_id = $2",
                    "tamper",
                    organization_one_id,
                )
            with pytest.raises(asyncpg.CheckViolationError, match="audit events are append only"):
                await migrator.execute(
                    "DELETE FROM audit_events WHERE organization_id = $1",
                    organization_one_id,
                )
        finally:
            await migrator.close()

    asyncio.run(scenario())
