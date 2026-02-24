"""Add observability_snapshots table

Revision ID: b4e8f2a71c03
Revises: a1b7c3d5e9f2
Create Date: 2026-02-23 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b4e8f2a71c03"
down_revision = "a1b7c3d5e9f2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "observability_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("cpu_usage_m", sa.Float(), nullable=True),
        sa.Column("memory_usage_bytes", sa.BigInteger(), nullable=True),
        sa.Column("pod_count", sa.Integer(), nullable=True),
        sa.Column("restart_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["project_applications.id"],
            name=op.f("fk_observability_snapshots_application_id_project_applications"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observability_snapshots")),
    )
    op.create_index(
        op.f("ix_observability_snapshots_application_id"),
        "observability_snapshots",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_observability_snapshots_timestamp"),
        "observability_snapshots",
        ["timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_observability_snapshots_app_ts",
        "observability_snapshots",
        ["application_id", "timestamp"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_observability_snapshots_app_ts",
        table_name="observability_snapshots",
    )
    op.drop_index(
        op.f("ix_observability_snapshots_timestamp"),
        table_name="observability_snapshots",
    )
    op.drop_index(
        op.f("ix_observability_snapshots_application_id"),
        table_name="observability_snapshots",
    )
    op.drop_table("observability_snapshots")
