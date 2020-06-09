import asyncio
from argparse import ArgumentParser
from datetime import datetime, timedelta
from os import environ

import pandas as pd
import pytz
from aiohttp import WSMsgType, web
from sqlalchemy import create_engine
from sqlalchemy.sql import text

routes = web.RouteTableDef()


async def create_sqlalchemy(app):
    app["sql_engine"] = create_engine("postgresql://thermnet@localhost/thermnet")


async def dispose_sqlalchemy(app):
    app["sql_engine"].dispose()


def last(df: pd.DataFrame, period, resolution):
    return (
        df[df.index > datetime.now(pytz.utc) - period]
        .resample(resolution)
        .mean()
        .interpolate()
    )


@routes.post("/measurements/")
async def measurements(request: web.Request):
    shared_secret = request.app["shared_secret"]

    data = await request.json()

    if not data or "key" not in data or "data" not in data or "time" not in data:
        raise web.HTTPBadRequest()

    if data["key"] != shared_secret:
        raise web.HTTPUnauthorized()

    time = datetime.utcfromtimestamp((await request.json())["time"])
    temp = data["data"]

    async with request.app["events_lock"]:
        request.app["current_temp"] = temp
        for event in request.app["events"]:
            event.set()

    s = text("INSERT INTO measurements (time, value) VALUES (:time, :temp)")
    with request.app["sql_engine"].connect() as conn:
        conn.execute(
            s, time=time, temp=temp,
        )

    return web.Response(status=200)


@routes.get("/ws/")
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    temp = request.app["current_temp"]
    if temp is not None:
        await ws.send_json({"type": "last", "data": temp})

    s = text("""SELECT date_trunc('minute', time) AS time, avg(value) as value
        FROM measurements WHERE time > :nt GROUP BY 1""")
    with request.app["sql_engine"].connect() as conn:
        data = conn.execute(s, nt=datetime.now(pytz.utc) - timedelta(days=2)).fetchall()

    if temp is None:
        await ws.send_json({"type": "last", "data": data[-1][1]})

    df = pd.DataFrame(data, columns=["time", "temperature"])
    df = df.set_index("time")
    df = df["temperature"]

    await ws.send_str(
        '{"type": "24h", "data": '
        + last(df, timedelta(days=1), "5min").to_json(orient="split")
        + "}"
    )

    await ws.send_str(
        '{"type": "48h", "data": '
        + last(df, timedelta(days=2), "10min").to_json(orient="split")
        + "}"
    )

    s = text("""SELECT date_trunc('hour', time) AS time, avg(value) as value
        FROM measurements WHERE time > :nt GROUP BY 1""")
    with request.app["sql_engine"].connect() as conn:
        data = conn.execute(s, nt=datetime.now(pytz.utc) - timedelta(weeks=1)).fetchall()

    df = pd.DataFrame(data, columns=["time", "temperature"])
    df = df.set_index("time")
    df = df["temperature"]

    await ws.send_str(
        '{"type": "1w", "data": '
        + df.to_json(orient="split")
        + "}"
    )

    event = asyncio.Event()
    async with request.app["events_lock"]:
        request.app["events"].append(event)
    try:
        while True:
            await event.wait()
            async with request.app["events_lock"]:
                temp = request.app["current_temp"]
            await ws.send_json({"type": "last", "data": temp})
            event.clear()
    finally:
        request.app["events"].remove(event)
        await ws.close()
        return ws


async def app(argv=None):
    application = web.Application()

    application["shared_secret"] = environ["KEY"]
    application["current_temp"] = None
    application["events"] = []
    application["events_lock"] = asyncio.Lock()

    application.add_routes(routes)
    application.on_startup.append(create_sqlalchemy)
    application.on_cleanup.append(dispose_sqlalchemy)

    return application


if __name__ == "__main__":
    application = app()
    web.run_app(application, reuse_address=True, reuse_port=True)
