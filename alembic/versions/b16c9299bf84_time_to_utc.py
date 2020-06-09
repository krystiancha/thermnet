"""Time to UTC

Revision ID: b16c9299bf84
Revises: 3a4c5a7574d3
Create Date: 2020-05-18 18:47:37.579680

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b16c9299bf84'
down_revision = '3a4c5a7574d3'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        table_name="measurements",
        column_name="time",
        type_=sa.DateTime(timezone=True)
    )


def downgrade():
    op.alter_column(
        table_name="measurements",
        column_name="time",
        type_=sa.DateTime(timezone=False)
    )
