"""Add append-only tenant-scoped audit events.

Revision ID: 20260818_0002
Revises: 20260818_0001
Create Date: 2026-08-18 00:30:00+00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260818_0002"
down_revision = "20260818_0001"
branch_labels = None
depends_on = None

_RLS_POLICY_SQL = """
CREATE POLICY audit_events_tenant_isolation
ON audit_events
USING (organization_id = NULLIF(current_setting('asdo.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('asdo.organization_id', true), '')::uuid)
"""

_APPEND_ONLY_FUNCTION_SQL = """
CREATE FUNCTION reject_audit_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit events are append only'
        USING ERRCODE = '23514';
END;
$$
"""

_APPEND_ONLY_UPDATE_TRIGGER_SQL = """
CREATE TRIGGER audit_events_append_only_update
BEFORE UPDATE ON audit_events
FOR EACH ROW
EXECUTE FUNCTION reject_audit_event_mutation()
"""

_APPEND_ONLY_DELETE_TRIGGER_SQL = """
CREATE TRIGGER audit_events_append_only_delete
BEFORE DELETE ON audit_events
FOR EACH ROW
EXECUTE FUNCTION reject_audit_event_mutation()
"""


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column(
            "sequence_id",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=127), nullable=False),
        sa.Column("resource_type", sa.String(length=127), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("previous_event_hash", sa.String(length=64), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "outcome IN ('success', 'failure', 'denied')",
            name="ck_audit_events_outcome",
        ),
        sa.CheckConstraint(
            "length(payload_hash) = 64 AND length(event_hash) = 64",
            name="ck_audit_events_hash_lengths",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_audit_events_org",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("sequence_id", name="pk_audit_events"),
        sa.UniqueConstraint("id", name="uq_audit_events_id"),
        sa.UniqueConstraint("event_hash", name="uq_audit_events_event_hash"),
    )
    op.create_index(
        "ix_audit_events_organization_id",
        "audit_events",
        ["organization_id"],
        unique=False,
    )
    op.execute("ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_events FORCE ROW LEVEL SECURITY")
    op.execute(_RLS_POLICY_SQL)
    op.execute(_APPEND_ONLY_FUNCTION_SQL)
    op.execute(_APPEND_ONLY_UPDATE_TRIGGER_SQL)
    op.execute(_APPEND_ONLY_DELETE_TRIGGER_SQL)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_events_append_only_delete ON audit_events")
    op.execute("DROP TRIGGER IF EXISTS audit_events_append_only_update ON audit_events")
    op.execute("DROP FUNCTION IF EXISTS reject_audit_event_mutation()")
    op.execute("DROP POLICY audit_events_tenant_isolation ON audit_events")
    op.drop_table("audit_events")
