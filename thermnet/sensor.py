import thermnet.bme280
import smbus
import sqlalchemy as sa
from datetime import datetime
import os
import logging
from dataclasses import dataclass
import sys
import argparse


@dataclass
class Sensor:
    HELP = "The format is: \"id1 bus1 address1,id2 bus2 address2,...\""
    id: int
    bus: int
    address: hex

    @classmethod
    def from_str(cls, s: str):
        spl = s.split()
        if len(spl) != 3:
            raise ValueError(f"Bad format: {s}")
        raw_id, raw_bus, raw_address = spl
        try:
            id = int(raw_id)
        except ValueError:
            raise ValueError(f"Bad id: {raw_id}")
        try:
            bus = int(raw_bus)
        except ValueError:
            raise ValueError(f"Bad bus: {raw_bus}")
        try:
            address = int(raw_address, 0)
        except (ValueError, TypeError):
            raise ValueError(f"Bad address: {raw_address}")
        
        return Sensor(id, bus, address)
    
    
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")


def main(args=None):
    logging.basicConfig(
        format="%(levelname)s:%(message)s",
        level=os.environ.get("LOG_LEVEL", "INFO"),
    )

    args = parser.parse_args(args)
    
    DB_URL = os.environ.get("DB_URL", "postgresql://thermnet@localhost/thermnet")
    logging.info(f"Database URL: {DB_URL}")

    try:
        SENSORS = map(
            lambda x: Sensor.from_str(x),
            os.environ.get("SENSORS", "0 1 0x76").split(","),
        )
    except ValueError as e:
        logging.error(f"Bad SENSORS config: {e}; {Sensor.HELP}")
        sys.exit(1)

    for sensor in SENSORS:
        logging.info(f"Reading sensor: {sensor}")

        try:
            i2c = smbus.SMBus(sensor.bus)
        except FileNotFoundError:
            logging.error(f"Bus {sensor.bus} not found")
            sys.exit(1)

        bme = thermnet.bme280.Adafruit_BME280_I2C(i2c, sensor.address)

        t, p, h = (bme.temperature, bme.pressure, bme.humidity)
        logging.info(f"Got {t}, {p}, {h}")

        if args.check:
            continue

        with sa.create_engine(DB_URL).connect() as conn:
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
                sensor=sensor.id,
                temperature=bme.temperature,
                pressure=bme.pressure,
                humidity=bme.humidity,
            )
            logging.info("Committed to database")
            

if __name__ == "__main__":
    main()
