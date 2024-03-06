"""empty message

Revision ID: e11c61ce67e7
Revises: 5db306adc6cc
Create Date: 2018-04-17 08:27:07.852716

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e11c61ce67e7"
down_revision = "5db306adc6cc"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "project_applications",
        sa.Column(
            "process_pod_classes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("json_object('{}')"),
            nullable=True,
        ),
    )
    op.add_column(
        "project_applications_version",
        sa.Column(
            "process_pod_classes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("json_object('{}')"),
            autoincrement=False,
            nullable=True,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("project_applications_version", "process_pod_classes")
    op.drop_column("project_applications", "process_pod_classes")
    # ### end Alembic commands ###
