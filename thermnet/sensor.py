import thermnet.bme280
import smbus
import sqlalchemy as sa
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--sensor", required=True)
args = parser.parse_args()

i2c = smbus.SMBus(1)
bme280 = thermnet.bme280.Adafruit_BME280_I2C(i2c)

with sa.create_engine("postgresql://thermnet@localhost/thermnet").connect() as conn:
    conn.execute(
        sa.text(
            """
            INSERT INTO measurements (time, value, sensor, quantity) VALUES
            (:time, :temperature, :sensor, 1),
            (:time, :pressure, :sensor, 2),
            (:time, :humidity, :sensor, 3)
        """
        ),
        time=datetime.utcnow(),
        sensor=args.sensor,
        temperature=bme280.temperature,
        pressure=bme280.pressure,
        humidity=bme280.humidity,
    )
