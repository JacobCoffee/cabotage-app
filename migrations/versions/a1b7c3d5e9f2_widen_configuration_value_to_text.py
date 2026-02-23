"""Widen Configuration.value from varchar(2048) to text

Revision ID: a1b7c3d5e9f2
Revises: c2ae2e19e1f2
Create Date: 2026-02-23 23:50:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "a1b7c3d5e9f2"
down_revision = "c2ae2e19e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "project_app_configurations",
        "value",
        existing_type=sa.String(2048),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "project_app_configurations_version",
        "value",
        existing_type=sa.String(2048),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "project_app_configurations_version",
        "value",
        existing_type=sa.Text(),
        type_=sa.String(2048),
        existing_nullable=True,
    )
    op.alter_column(
        "project_app_configurations",
        "value",
        existing_type=sa.Text(),
        type_=sa.String(2048),
        existing_nullable=False,
    )
