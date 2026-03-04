import logging
import secrets
from pathlib import Path
from datetime import datetime, timedelta

from aiohttp import web

from bot.config import settings
from bot.services.yandex_api import get_cached_coefficients, get_top_zones
from bot.services.zones import get_zones
from bot.services.hex_grid import hex_grid_json
from bot.services.payment import process_payment_webhook
from bot.services.admin import get_dashboard_stats, get_recent_users, get_top_earners, search_users, get_user_details, grant_subscription, reset_user_data, delete_user_permanently, get_all_user_ids
from bot.services.game import submit_game_score

logger = logging.getLogger(__name__)

# Simple token storage (in production use Redis or database)
admin_tokens = {}

WEBAPP_DIR = Path(__file__).resolve().parent.parent.parent / "webapp"


async def index(_request: web.Request) -> web.FileResponse:
    import time
    # Add timestamp to force cache refresh
    html_content = (WEBAPP_DIR / "index.html").read_text(encoding='utf-8')
    timestamp = int(time.time())
    html_content = html_content.replace('app.js?v=3', f'app.js?v={timestamp}')

    response = web.Response(text=html_content, content_type='text/html', charset='utf-8')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


async def static_file(request: web.Request) -> web.FileResponse:
    name = request.match_info["name"]
    path = WEBAPP_DIR / name
    if not path.is_file() or not path.resolve().is_relative_to(WEBAPP_DIR):
        raise web.HTTPNotFound()
    response = web.FileResponse(path)
    # Don't cache for HTML/JS/CSS, but allow caching for documents
    if not name.endswith('.docx'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


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
    response = web.json_response(result)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


async def api_zones(_request: web.Request) -> web.Response:
    zones = get_zones()
    response = web.json_response([
        {"id": z.id, "name": z.name, "lat": z.lat, "lon": z.lon, "radius_km": z.radius_km}
        for z in zones
    ])
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


async def api_top(request: web.Request) -> web.Response:
    n = int(request.query.get("n", "5"))
    tariff = request.query.get("tariff")
    top = get_top_zones(n=n, tariff=tariff or None)
    zones_map = {z.id: z.name for z in get_zones()}
    response = web.json_response([
        {"zone_id": d.zone_id, "zone_name": zones_map.get(d.zone_id, d.zone_id),
         "tariff": d.tariff, "coefficient": d.coefficient}
        for d in top
    ])
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


async def api_hexgrid(request: web.Request) -> web.Response:
    tariff = request.query.get("tariff")
    data = hex_grid_json(tariff=tariff or None)
    response = web.json_response(data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


async def api_user_subscription(request: web.Request) -> web.Response:
    """Get user subscription status for webapp."""
    try:
        # Get telegram user ID from query or initData
        telegram_id = request.query.get("telegram_id")

        if not telegram_id:
            # Try to parse from Telegram WebApp initData
            init_data = request.query.get("initData", "")
            logger.info(f"Received initData: {init_data[:100] if init_data else 'empty'}")

            if init_data:
                # Parse initData to extract user info
                # Format: query_id=...&user={"id":123,...}&...
                import urllib.parse
                import json
                params = urllib.parse.parse_qs(init_data)
                user_json = params.get("user", [None])[0]
                logger.info(f"Parsed user JSON: {user_json[:100] if user_json else 'none'}")

                if user_json:
                    user_data = json.loads(user_json)
                    telegram_id = user_data.get("id")
                    logger.info(f"Extracted telegram_id: {telegram_id}")

        if not telegram_id:
            logger.warning("No telegram_id found, returning free access")
            # Return default free access if no user ID
            return web.json_response({
                "has_business_access": False,
                "tier": "free"
            })

        # Check subscription
        from bot.services.subscription import check_feature_access, get_subscription
        telegram_id = int(telegram_id)
        has_business = await check_feature_access(telegram_id, "business_tariff")
        subscription = await get_subscription(telegram_id)

        logger.info(f"User {telegram_id} subscription: tier={subscription.tier}, has_business={has_business}")

        response = web.json_response({
            "has_business_access": has_business,
            "tier": subscription.tier
        })
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    except Exception as e:
        logger.error(f"Error checking user subscription: {e}", exc_info=True)
        # Return free access on error
        return web.json_response({
            "has_business_access": False,
            "tier": "free"
        })


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


# Admin panel endpoints
async def admin_login_page(request: web.Request) -> web.FileResponse:
    """Serve admin login page."""
    return web.FileResponse(WEBAPP_DIR / "admin_login.html")


async def admin_dashboard_page(request: web.Request) -> web.FileResponse:
    """Serve admin dashboard page."""
    return web.FileResponse(WEBAPP_DIR / "admin_dashboard.html")


async def admin_login(request: web.Request) -> web.Response:
    """Handle admin login."""
    try:
        data = await request.json()
        password = data.get("password")

        if password == settings.admin_password:
            # Generate token
            token = secrets.token_urlsafe(32)
            admin_tokens[token] = datetime.now() + timedelta(hours=24)

            logger.info("Admin login successful")
            return web.json_response({"success": True, "token": token})
        else:
            logger.warning("Admin login failed: incorrect password")
            return web.json_response({"success": False, "error": "Неверный пароль"})

    except Exception as e:
        logger.error(f"Admin login error: {e}")
        return web.json_response({"success": False, "error": "Ошибка сервера"}, status=500)


def check_admin_token(request: web.Request) -> bool:
    """Check if request has valid admin token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False

    token = auth_header[7:]
    expiry = admin_tokens.get(token)

    if not expiry:
        return False

    if datetime.now() > expiry:
        del admin_tokens[token]
        return False

    return True


async def admin_stats(request: web.Request) -> web.Response:
    """Get admin dashboard statistics."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        stats = await get_dashboard_stats()
        return web.json_response(stats)
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_recent_users(request: web.Request) -> web.Response:
    """Get recent users."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        users = await get_recent_users(limit=10)
        return web.json_response(users)
    except Exception as e:
        logger.error(f"Error getting recent users: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_top_earners(request: web.Request) -> web.Response:
    """Get top earning users."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        earners = await get_top_earners(limit=10)
        return web.json_response(earners)
    except Exception as e:
        logger.error(f"Error getting top earners: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_search_users(request: web.Request) -> web.Response:
    """Search users by username or telegram_id."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        query = request.query.get("q", "")
        if not query:
            return web.json_response({"error": "Query parameter required"}, status=400)

        users = await search_users(query)
        return web.json_response(users)
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_user_details(request: web.Request) -> web.Response:
    """Get detailed user information."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        telegram_id = int(request.match_info["telegram_id"])
        details = await get_user_details(telegram_id)

        if not details:
            return web.json_response({"error": "User not found"}, status=404)

        return web.json_response(details)
    except ValueError:
        return web.json_response({"error": "Invalid telegram_id"}, status=400)
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_grant_subscription(request: web.Request) -> web.Response:
    """Grant subscription to user."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        data = await request.json()
        telegram_id = int(data.get("telegram_id"))
        tier = data.get("tier")
        duration_days = int(data.get("duration_days", 30))

        if tier not in ["pro", "premium", "elite"]:
            return web.json_response({"error": "Invalid tier"}, status=400)

        success = await grant_subscription(telegram_id, tier, duration_days)

        if success:
            logger.info(f"Admin granted {tier} subscription to user {telegram_id}")
            return web.json_response({"success": True})
        else:
            return web.json_response({"error": "Failed to grant subscription"}, status=500)

    except Exception as e:
        logger.error(f"Error granting subscription: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_reset_user(request: web.Request) -> web.Response:
    """Reset user data to initial state."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        data = await request.json()
        telegram_id = int(data.get("telegram_id"))

        success = await reset_user_data(telegram_id)

        if success:
            logger.info(f"Admin reset user data for {telegram_id}")
            return web.json_response({"success": True})
        else:
            return web.json_response({"error": "Failed to reset user"}, status=500)

    except Exception as e:
        logger.error(f"Error resetting user: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_delete_user(request: web.Request) -> web.Response:
    """Permanently delete user from database."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        data = await request.json()
        telegram_id = int(data.get("telegram_id"))

        success = await delete_user_permanently(telegram_id)

        if success:
            logger.info(f"Admin permanently deleted user {telegram_id}")
            return web.json_response({"success": True})
        else:
            return web.json_response({"error": "Failed to delete user"}, status=500)

    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_broadcast(request: web.Request) -> web.Response:
    """Send broadcast message to all users."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        data = await request.json()
        message = data.get("message", "").strip()

        if not message:
            return web.json_response({"error": "Message is required"}, status=400)

        # Get bot instance from app state
        bot = request.app.get("bot")
        if not bot:
            return web.json_response({"error": "Bot not available"}, status=500)

        # Get all user IDs
        user_ids = await get_all_user_ids()

        success_count = 0
        failed_count = 0

        # Send message to all users
        for user_id in user_ids:
            try:
                await bot.send_message(user_id, message, parse_mode="HTML")
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user_id}: {e}")
                failed_count += 1

        logger.info(f"Admin broadcast completed: {success_count} success, {failed_count} failed")

        return web.json_response({
            "success": True,
            "total": len(user_ids),
            "sent": success_count,
            "failed": failed_count
        })

    except Exception as e:
        logger.error(f"Error sending broadcast: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def game_index(_request: web.Request) -> web.FileResponse:
    """Serve game page."""
    response = web.FileResponse(WEBAPP_DIR / "game" / "index.html")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


async def api_game_submit_score(request: web.Request) -> web.Response:
    """Handle game score submission."""
    try:
        data = await request.json()
        score = int(data.get("score", 0))
        init_data = data.get("initData", "")

        if not init_data:
            return web.json_response({"success": False, "error": "Отсутствуют данные авторизации"}, status=400)

        result = await submit_game_score(score, init_data)
        return web.json_response(result)

    except ValueError:
        return web.json_response({"success": False, "error": "Неверный формат данных"}, status=400)
    except Exception as e:
        logger.error(f"Error submitting game score: {e}")
        return web.json_response({"success": False, "error": "Ошибка сервера"}, status=500)


async def admin_promo_codes(request: web.Request) -> web.Response:
    """Get all promo codes."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        from bot.services.promo_code import get_all_promo_codes

        promo_codes = await get_all_promo_codes()

        result = []
        for promo in promo_codes:
            result.append({
                "id": promo.id,
                "code": promo.code,
                "tier": promo.tier,
                "duration_days": promo.duration_days,
                "max_uses": promo.max_uses,
                "current_uses": promo.current_uses,
                "uses_remaining": promo.uses_remaining,
                "is_active": promo.is_active,
                "is_valid": promo.is_valid,
                "valid_from": promo.valid_from.isoformat(),
                "valid_until": promo.valid_until.isoformat() if promo.valid_until else None,
                "description": promo.description,
                "created_at": promo.created_at.isoformat()
            })

        return web.json_response(result)

    except Exception as e:
        logger.error(f"Error fetching promo codes: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_create_promo_code(request: web.Request) -> web.Response:
    """Create new promo code."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        from bot.services.promo_code import create_promo_code
        from datetime import datetime

        data = await request.json()
        code = data.get("code", "").strip().upper()
        tier = data.get("tier")
        duration_days = int(data.get("duration_days", 30))
        max_uses = data.get("max_uses")
        valid_until_str = data.get("valid_until")
        description = data.get("description")

        if not code or not tier:
            return web.json_response({"error": "Code and tier are required"}, status=400)

        if tier not in ["pro", "premium", "elite"]:
            return web.json_response({"error": "Invalid tier"}, status=400)

        if max_uses is not None:
            max_uses = int(max_uses)

        valid_until = None
        if valid_until_str:
            valid_until = datetime.fromisoformat(valid_until_str)

        promo = await create_promo_code(
            code=code,
            tier=tier,
            duration_days=duration_days,
            max_uses=max_uses,
            valid_until=valid_until,
            description=description
        )

        logger.info(f"Admin created promo code: {code}")

        return web.json_response({
            "success": True,
            "promo_code": {
                "id": promo.id,
                "code": promo.code,
                "tier": promo.tier,
                "duration_days": promo.duration_days
            }
        })

    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating promo code: {e}")
        return web.json_response({"error": "Server error"}, status=500)


async def admin_deactivate_promo_code(request: web.Request) -> web.Response:
    """Deactivate promo code."""
    if not check_admin_token(request):
        return web.json_response({"error": "Unauthorized"}, status=401)

    try:
        from bot.services.promo_code import deactivate_promo_code

        data = await request.json()
        code = data.get("code", "").strip().upper()

        if not code:
            return web.json_response({"error": "Code is required"}, status=400)

        success = await deactivate_promo_code(code)

        if success:
            logger.info(f"Admin deactivated promo code: {code}")
            return web.json_response({"success": True})
        else:
            return web.json_response({"error": "Promo code not found"}, status=404)

    except Exception as e:
        logger.error(f"Error deactivating promo code: {e}")
        return web.json_response({"error": "Server error"}, status=500)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/api/coefficients", api_coefficients)
    app.router.add_get("/api/zones", api_zones)
    app.router.add_get("/api/top", api_top)
    app.router.add_get("/api/hexgrid", api_hexgrid)
    app.router.add_get("/api/user/subscription", api_user_subscription)
    app.router.add_post("/webhook/yookassa", webhook_yookassa)

    # Game routes
    app.router.add_get("/game", game_index)
    app.router.add_post("/api/game/submit-score", api_game_submit_score)

    # Admin panel routes
    app.router.add_get("/admin/login", admin_login_page)
    app.router.add_get("/admin/dashboard", admin_dashboard_page)
    app.router.add_post("/admin/login", admin_login)
    app.router.add_get("/admin/api/stats", admin_stats)
    app.router.add_get("/admin/api/recent-users", admin_recent_users)
    app.router.add_get("/admin/api/top-earners", admin_top_earners)
    app.router.add_get("/admin/api/search-users", admin_search_users)
    app.router.add_get("/admin/api/user/{telegram_id}", admin_user_details)
    app.router.add_post("/admin/api/grant-subscription", admin_grant_subscription)
    app.router.add_post("/admin/api/reset-user", admin_reset_user)
    app.router.add_post("/admin/api/delete-user", admin_delete_user)
    app.router.add_post("/admin/api/broadcast", admin_broadcast)

    # Promo code routes
    app.router.add_get("/admin/api/promo-codes", admin_promo_codes)
    app.router.add_post("/admin/api/promo-codes/create", admin_create_promo_code)
    app.router.add_post("/admin/api/promo-codes/deactivate", admin_deactivate_promo_code)

    app.router.add_get("/{name}", static_file)
    return app
