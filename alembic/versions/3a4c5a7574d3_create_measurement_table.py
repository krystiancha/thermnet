"""create measurement table

Revision ID: 3a4c5a7574d3
Revises:
Create Date: 2020-05-15 18:54:12.417881

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3a4c5a7574d3"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "measurements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("time", sa.DateTime, nullable=False),
        sa.Column("value", sa.Float, nullable=False),
    )


def downgrade():
    op.drop_table("measurements")
