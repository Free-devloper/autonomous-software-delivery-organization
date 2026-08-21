"""Create organization tenancy records and default-deny RLS.

Revision ID: 20260818_0001
Revises:
Create Date: 2026-08-18 00:00:00+00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20260818_0001"
down_revision = None
branch_labels = None
depends_on = None

_RLS_POLICY_SQL = """
CREATE POLICY organization_configurations_tenant_isolation
ON organization_configurations
USING (organization_id = NULLIF(current_setting('asdo.organization_id', true), '')::uuid)
WITH CHECK (organization_id = NULLIF(current_setting('asdo.organization_id', true), '')::uuid)
"""

_ID_IMMUTABILITY_FUNCTION_SQL = """
CREATE FUNCTION reject_organization_configuration_id_change()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.id IS DISTINCT FROM OLD.id THEN
        RAISE EXCEPTION 'organization configuration id is immutable'
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$$
"""

_ID_IMMUTABILITY_TRIGGER_SQL = """
CREATE TRIGGER organization_configurations_id_immutable
BEFORE UPDATE ON organization_configurations
FOR EACH ROW
EXECUTE FUNCTION reject_organization_configuration_id_change()
"""


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=63), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organizations"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_table(
        "organization_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data_region", sa.String(length=63), nullable=False),
        sa.Column("data_classification", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "data_classification IN ('public', 'internal', 'confidential', 'restricted')",
            name="ck_organization_configurations_data_classification",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_organization_configurations_org",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_organization_configurations"),
        sa.UniqueConstraint("organization_id", name="uq_organization_configurations_org"),
    )
    op.create_index(
        "ix_organization_configurations_organization_id",
        "organization_configurations",
        ["organization_id"],
        unique=False,
    )
    op.execute("ALTER TABLE organization_configurations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE organization_configurations FORCE ROW LEVEL SECURITY")
    op.execute(_RLS_POLICY_SQL)
    op.execute(_ID_IMMUTABILITY_FUNCTION_SQL)
    op.execute(_ID_IMMUTABILITY_TRIGGER_SQL)


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS organization_configurations_id_immutable "
        "ON organization_configurations"
    )
    op.execute("DROP FUNCTION IF EXISTS reject_organization_configuration_id_change()")
    op.execute(
        "DROP POLICY organization_configurations_tenant_isolation ON organization_configurations"
    )
    op.drop_table("organization_configurations")
    op.drop_table("organizations")
