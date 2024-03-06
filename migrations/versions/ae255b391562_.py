"""empty message

Revision ID: ae255b391562
Revises: 9ec01c7ff255
Create Date: 2023-02-24 13:22:49.563815

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ae255b391562"
down_revision = "9ec01c7ff255"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "deployments", sa.Column("job_id", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "deployments_version",
        sa.Column("job_id", sa.String(length=64), autoincrement=False, nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("deployments_version", "job_id")
    op.drop_column("deployments", "job_id")
    # ### end Alembic commands ###
