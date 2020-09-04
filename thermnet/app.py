import asyncio
from datetime import datetime
from json.decoder import JSONDecodeError

from aiohttp import web
from sqlalchemy import create_engine
from sqlalchemy.sql import text

routes = web.RouteTableDef()


async def create_sqlalchemy(app):
    app["sql_engine"] = create_engine("postgresql://thermnet@localhost/thermnet")


async def get_first_current(app):
    with app["sql_engine"].connect() as conn:
        for id, name in {1: "temperature", 2: "pressure", 3: "humidity"}.items():
            result = conn.execute(
                text(
                    """
                    SELECT value FROM measurements
                    WHERE quantity = :id ORDER BY time DESC LIMIT 1;
                """
                ),
                id=id,
            )
            async with app["current_cond"]:
                try:
                    app["current"][name] = float(next(result)[0])
                except StopIteration:
                    pass


async def dispose_sqlalchemy(app):
    app["sql_engine"].dispose()


@routes.post("/measurements/")
async def measurements(request: web.Request):
    try:
        data = await request.json()
    except JSONDecodeError as e:
        raise web.HTTPBadRequest(reason=f"JSON decode error: {e}")

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
            request.app["current"] = {
                x: float(data[x]) for x in ["temperature", "pressure", "humidity"]
            }
            request.app["current_cond"].notify_all()

    except KeyError as e:
        raise web.HTTPBadRequest(reason=f"Key error: {e}")

    return web.Response(status=200)


@routes.get("/ws/")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async with request.app["current_cond"]:
        current = request.app["current"]

    try:
        while True:
            await ws.send_json(current)
            async with request.app["current_cond"]:
                await request.app["current_cond"].wait()
                current = request.app["current"]
    finally:
        await ws.close()
        return ws


async def app(args=None):
    application = web.Application()

    application["current"] = {}
    application["current_cond"] = asyncio.Condition()

    application.add_routes(routes)
    application.on_startup.append(create_sqlalchemy)
    application.on_startup.append(get_first_current)
    application.on_cleanup.append(dispose_sqlalchemy)

    return application


if __name__ == "__main__":
    application = app()
    web.run_app(application, reuse_address=True, reuse_port=True)
