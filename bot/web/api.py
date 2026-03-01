import logging
from pathlib import Path

from aiohttp import web

from bot.services.yandex_api import get_cached_coefficients, get_top_zones
from bot.services.zones import get_zones
from bot.services.hex_grid import hex_grid_json
from bot.services.payment import process_payment_webhook

logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).resolve().parent.parent.parent / "webapp"


async def index(_request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEBAPP_DIR / "index.html")


async def static_file(request: web.Request) -> web.FileResponse:
    name = request.match_info["name"]
    path = WEBAPP_DIR / name
    if not path.is_file() or not path.resolve().is_relative_to(WEBAPP_DIR):
        raise web.HTTPNotFound()
    return web.FileResponse(path)


async def api_coefficients(_request: web.Request) -> web.Response:
    zones_map = {z.id: {"name": z.name, "lat": z.lat, "lon": z.lon, "radius_km": z.radius_km} for z in get_zones()}
    data = get_cached_coefficients()
    result = []
    for d in data:
        zone_info = zones_map.get(d.zone_id, {})
        result.append({
            "zone_id": d.zone_id,
            "tariff": d.tariff,
            "coefficient": d.coefficient,
            "timestamp": d.timestamp,
            **zone_info,
        })
    return web.json_response(result)


async def api_zones(_request: web.Request) -> web.Response:
    zones = get_zones()
    return web.json_response([
        {"id": z.id, "name": z.name, "lat": z.lat, "lon": z.lon, "radius_km": z.radius_km}
        for z in zones
    ])


async def api_top(request: web.Request) -> web.Response:
    n = int(request.query.get("n", "5"))
    tariff = request.query.get("tariff")
    top = get_top_zones(n=n, tariff=tariff or None)
    zones_map = {z.id: z.name for z in get_zones()}
    return web.json_response([
        {"zone_id": d.zone_id, "zone_name": zones_map.get(d.zone_id, d.zone_id),
         "tariff": d.tariff, "coefficient": d.coefficient}
        for d in top
    ])


async def api_hexgrid(request: web.Request) -> web.Response:
    tariff = request.query.get("tariff")
    data = hex_grid_json(tariff=tariff or None)
    return web.json_response(data)


async def webhook_yookassa(request: web.Request) -> web.Response:
    """Handle YooKassa payment webhook."""
    try:
        webhook_data = await request.json()
        logger.info(f"Received YooKassa webhook: {webhook_data.get('event')}")

        success = await process_payment_webhook(webhook_data)

        if success:
            return web.json_response({"status": "ok"})
        else:
            return web.json_response({"status": "error"}, status=400)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/api/coefficients", api_coefficients)
    app.router.add_get("/api/zones", api_zones)
    app.router.add_get("/api/top", api_top)
    app.router.add_get("/api/hexgrid", api_hexgrid)
    app.router.add_post("/webhook/yookassa", webhook_yookassa)
    app.router.add_get("/{name}", static_file)
    return app
