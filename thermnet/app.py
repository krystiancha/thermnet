import argparse
import asyncio
import configparser
import logging
from datetime import datetime
from itertools import groupby
from json.decoder import JSONDecodeError

from aiohttp import web
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from thermnet.logging import setup_logging

routes = web.RouteTableDef()

parser = argparse.ArgumentParser()
parser.add_argument("--config", default="/etc/thermnet/thermnet.ini")
parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default=8081, type=int)

config = configparser.ConfigParser()
config.read_dict(
    {
        "db": {"url": "postgresql://thermnet@localhost/thermnet"},
        "logging": {"level": "INFO"},
    }
)


async def get_payload(app):
    with app["sql_engine"].connect() as conn:
        quantities = {
            id: {"name": name, "unit": unit}
            for id, name, unit in conn.execute(
                text("""SELECT id, name, unit FROM quantities""")
            )
        }
        measurements = conn.execute(
            text(
                """
                SELECT id, time, value, sensor, quantity FROM measurements
                WHERE sensor = 0 AND time BETWEEN NOW() - INTERVAL '24 HOURS' AND NOW()
                ORDER BY time
                """
            )
        )

        app["logger"].info("Fetched payload")

        def q_key(x):
            return x[4]

        return [
            {
                "name": quantities[quantity]["name"],
                "unit": quantities[quantity]["unit"],
                "measurements": [
                    {"index": int(round(x[1].timestamp())), "value": x[2]}
                    for x in measurements
                ],
            }
            for quantity, measurements in groupby(
                sorted(measurements, key=q_key), key=q_key
            )
        ]


async def create_sqlalchemy(app):
    app["sql_engine"] = create_engine(app["db_url"])


async def init_payload(app):
    app["current_cond"] = asyncio.Condition()


async def dispose_sqlalchemy(app):
    app["sql_engine"].dispose()


@routes.post("/measurements/")
async def measurements(request: web.Request):
    try:
        data = await request.json()
    except JSONDecodeError as e:
        raise web.HTTPBadRequest(reason=f"JSON decode error: {e}")

    logging.info(f"Got request: {data}")

    try:
        with request.app["sql_engine"].connect() as conn:
            sensor_result = conn.execute(
                text("SELECT id FROM sensors WHERE secret = :secret"),
                secret=data["secret"],
            )
            sensor_id = next(sensor_result)[0]
    except KeyError as e:
        raise web.HTTPBadRequest(reason=f"Key error: {e}")
    except StopIteration:
        raise web.HTTPUnauthorized()

    logging.info(f"Selected sensor: {sensor_id}")

    try:
        with request.app["sql_engine"].connect() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO measurements (time, value, sensor, quantity) VALUES
                    (:time, :temperature, :sensor, 1),
                    (:time, :pressure, :sensor, 2),
                    (:time, :humidity, :sensor, 3)
                """
                ),
                time=datetime.utcnow(),
                sensor=sensor_id,
                temperature=data["temperature"],
                pressure=data["pressure"],
                humidity=data["humidity"],
            )
        async with request.app["current_cond"]:
            request.app["current_cond"].notify_all()

    except KeyError as e:
        raise web.HTTPBadRequest(reason=f"Key error: {e}")

    return web.Response(status=200)


@routes.get("/ws/")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    try:
        while True:
            try:
                payload = await get_payload(request.app)
            except Exception as e:
                logging.warning(f"Error while fetching payload: {e}")
                continue

            await ws.send_json(payload)
            async with request.app["current_cond"]:
                await request.app["current_cond"].wait()
    finally:
        await ws.close()
        return ws


async def app(config_path="/etc/thermnet/thermnet.ini"):
    config.read(config)
    setup_logging(config["logging"]["level"])

    application = web.Application()

    application["db_url"] = config["db"]["url"]

    application.add_routes(routes)
    application.on_startup.append(create_sqlalchemy)
    application.on_startup.append(init_payload)
    application.on_cleanup.append(dispose_sqlalchemy)

    return application


if __name__ == "__main__":
    args = parser.parse_args()

    web.run_app(
        app(args.config),
        host=args.host,
        port=args.port,
        reuse_address=True,
        reuse_port=True,
    )
