"""SQLAlchemy models for the Phase 0B tenancy foundation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from .identifiers import new_uuid7

DataClassification = Literal["public", "internal", "confidential", "restricted"]
AuditOutcome = Literal["success", "failure", "denied"]


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Base metadata used exclusively by explicit, reviewed Alembic migrations."""


UUIDv7PrimaryKey = Annotated[
    UUID,
    mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=new_uuid7),
]
CreatedAt = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
]
UpdatedAt = Annotated[
    datetime,
    mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
]


class Organization(Base):
    """The root boundary for a customer organization, not a tenant-owned record itself."""

    __tablename__ = "organizations"

    id: Mapped[UUIDv7PrimaryKey]
    slug: Mapped[str] = mapped_column(String(63), nullable=False, unique=True)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]


class TenantScopedModel:
    """Mixin requiring every child record to carry the authoritative organization ID."""

    @declared_attr
    def organization_id(cls) -> Mapped[UUID]:
        return mapped_column(
            PostgreSQLUUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )


class OrganizationConfiguration(TenantScopedModel, Base):
    """Persisted residency and classification policy, protected by forced PostgreSQL RLS."""

    __tablename__ = "organization_configurations"
    __table_args__ = (
        CheckConstraint(
            "data_classification IN ('public', 'internal', 'confidential', 'restricted')",
            name="ck_organization_configurations_data_classification",
        ),
        UniqueConstraint("organization_id", name="uq_organization_configurations_org"),
    )

    id: Mapped[UUIDv7PrimaryKey]
    data_region: Mapped[str] = mapped_column(String(63), nullable=False)
    data_classification: Mapped[DataClassification] = mapped_column(String(16), nullable=False)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]


class AuditEvent(TenantScopedModel, Base):
    """Append-only tenant-scoped security/audit event persisted under forced RLS."""

    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('success', 'failure', 'denied')",
            name="ck_audit_events_outcome",
        ),
        CheckConstraint(
            "length(payload_hash) = 64 AND length(event_hash) = 64",
            name="ck_audit_events_hash_lengths",
        ),
    )

    sequence_id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )
    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=new_uuid7,
    )
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(127), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(127), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    outcome: Mapped[AuditOutcome] = mapped_column(String(16), nullable=False)
    context: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    previous_event_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[CreatedAt]
