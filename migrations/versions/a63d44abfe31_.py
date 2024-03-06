"""empty message

Revision ID: a63d44abfe31
Revises: b3f0127e1ce2
Create Date: 2023-02-11 17:12:28.411560

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a63d44abfe31"
down_revision = "b3f0127e1ce2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "project_applications",
        sa.Column("github_environment_name", sa.Text(), nullable=True),
    )
    op.add_column(
        "project_applications_version",
        sa.Column(
            "github_environment_name", sa.Text(), autoincrement=False, nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("project_applications_version", "github_environment_name")
    op.drop_column("project_applications", "github_environment_name")
    # ### end Alembic commands ###
