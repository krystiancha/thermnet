"""add relations

Revision ID: c44759c383a1
Revises: b16c9299bf84
Create Date: 2020-08-31 19:22:44.005103

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c44759c383a1'
down_revision = 'b16c9299bf84'
branch_labels = None
depends_on = None


def upgrade():
    sensors = op.create_table(
      "sensors",
      sa.Column("id", sa.Integer, primary_key=True),
      sa.Column("name", sa.String, nullable=False),
      sa.Column("secret", sa.String, nullable=False),
    )
    op.bulk_insert(sensors, [{"id": 0, "name": "default sensor", "secret": "changeme"}])

    quantities = op.create_table(
        "quantities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("unit", sa.String, nullable=False),
    )
    op.bulk_insert(quantities, [
      {"id": 0, "name": "default quantity", "unit": ""},
      {"id": 1, "name": "temperature", "unit": "°C"},
      {"id": 2, "name": "pressure", "unit": "hPa"},
      {"id": 3, "name": "humidity", "unit": "%"},
    ])

    op.add_column("measurements", sa.Column("sensor", sa.Integer, sa.ForeignKey('sensors.id')))
    op.add_column("measurements", sa.Column("quantity", sa.Integer, sa.ForeignKey('quantities.id')))
    op.execute("UPDATE measurements SET sensor = 0 WHERE sensor IS NULL")
    op.execute("UPDATE measurements SET quantity = 0 WHERE quantity IS NULL")


def downgrade():
    op.drop_column("measurements", "sensor")
    op.drop_column("measurements", "quantity")
    op.drop_table("sensors")
    op.drop_table("quantities")
