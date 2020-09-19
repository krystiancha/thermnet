import argparse
import configparser
import logging
import re
from datetime import datetime

import smbus
import sqlalchemy as sa

import thermnet.bme280
from thermnet.logging import setup_logging

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="/etc/thermnet/thermnet.ini")
parser.add_argument("--check", action="store_true")

config = configparser.ConfigParser()
config.read_dict(
    {
        "db": {"url": "postgresql://thermnet@localhost/thermnet"},
        "logging": {"level": "INFO"},
    }
)


def main(args=None):
    args = parser.parse_args(args)
    config.read(args.config)

    setup_logging(config["logging"]["level"])

    if args.check and logging.getLogger().getEffectiveLevel() > logging.INFO:
        logging.warning("--check was specified, overriding log level to INFO")
        logging.getLogger().setLevel(logging.INFO)

    for section, kv in config.items():
        m = re.match("sensor-(.+)", section)
        if not m:
            continue
        try:
            sensor_id = int(m.group(1))
        except ValueError:
            logging.error(f"Invalid sensor ID: {m.group(1)}, skipping")
            continue

        try:
            bus = int(kv["bus"])
        except KeyError:
            logging.error(f"'bus' key not found in section {section}, skipping")
            continue
        except ValueError:
            logging.error(f"Invalid sensor bus: {kv['bus']}, skipping")
            continue

        try:
            address = int(kv["address"], 0)
        except KeyError:
            logging.error(f"'address' key not found in section {section}, skipping")
            continue
        except ValueError:
            logging.error(f"Invalid sensor address: {kv['address']}, skipping")
            continue

        logging.info(f"Found sensor {sensor_id} config: {hex(address)} @ bus {bus}")

        try:
            i2c = smbus.SMBus(bus)
        except FileNotFoundError:
            logging.error(f"Bus {bus} not found, skipping")
            continue

        try:
            bme = thermnet.bme280.Adafruit_BME280_I2C(i2c, address)
        except OSError as e:
            logging.error(f"{e}, please check sensor address: {address}, skipping")
            continue

        t, p, h = (bme.temperature, bme.pressure, bme.humidity)
        logging.info(f"Got data from sensor: {t:.2f} °C, {p:.2f} hPa, {h:.2f}%")

        if args.check:
            continue

        with sa.create_engine(config["db"]["url"]).connect() as conn:
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
                sensor=sensor_id,
                temperature=t,
                pressure=p,
                humidity=h,
            )
            logging.info("Committed to database")


if __name__ == "__main__":
    main()
