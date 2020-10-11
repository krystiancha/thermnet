"""create indexes

Revision ID: 5c6577394cbb
Revises: c44759c383a1
Create Date: 2020-10-11 18:53:07.650501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c6577394cbb'
down_revision = 'c44759c383a1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("measurements_idx", "measurements", ["time", "quantity", "sensor"])


def downgrade():
    op.drop_index("measurements_idx")
