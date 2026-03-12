"""
Service for geo-based alerts and notifications.
"""
import sqlite3
from typing import Optional, Tuple
from datetime import datetime
import math


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates in kilometers using Haversine formula.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


async def check_geo_alerts(user_id: int, latitude: float, longitude: float) -> Optional[str]:
    """
    Check for geo-based alerts near user's location.

    Args:
        user_id: User ID
        latitude: User's latitude
        longitude: User's longitude

    Returns:
        Alert message if any zones found, None otherwise
    """
    try:
        conn = sqlite3.connect("taxi-botbot.db")
        cursor = conn.cursor()

        # Create hot zones table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hot_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                latitude REAL,
                longitude REAL,
                coefficient REAL,
                radius_km REAL DEFAULT 2.0,
                active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Get active hot zones
        cursor.execute("""
            SELECT name, latitude, longitude, coefficient, radius_km
            FROM hot_zones
            WHERE active = 1
        """)

        zones = cursor.fetchall()
        conn.close()

        if not zones:
            return None

        # Find nearby zones
        nearby_zones = []
        for zone in zones:
            zone_name, zone_lat, zone_lon, coefficient, radius = zone
            distance = calculate_distance(latitude, longitude, zone_lat, zone_lon)

            if distance <= radius:
                nearby_zones.append({
                    'name': zone_name,
                    'distance': distance,
                    'coefficient': coefficient
                })

        if not nearby_zones:
            return None

        # Sort by coefficient (highest first)
        nearby_zones.sort(key=lambda x: x['coefficient'], reverse=True)

        # Get usage counter info
        tier = get_user_tier(user_id)
        daily_limit = get_alert_limit(user_id)

        # Get today's alert count
        cursor.execute("""
            SELECT COUNT(*) FROM alert_history
            WHERE user_id = ? AND DATE(sent_at) = DATE('now')
        """, (user_id,))
        alerts_sent_today = cursor.fetchone()[0]

        usage_info = f"\n📊 Использовано сегодня: {alerts_sent_today}/{daily_limit}"

        # Build alert message
        if len(nearby_zones) == 1:
            zone = nearby_zones[0]
            message = (
                f"🔥 <b>Выгодная зона рядом!</b>\n\n"
                f"📍 {zone['name']}\n"
                f"💰 Коэффициент: {zone['coefficient']:.1f}x\n"
                f"📏 Расстояние: {zone['distance']:.1f} км"
                f"{usage_info}"
            )
        else:
            message = f"🔥 <b>Найдено {len(nearby_zones)} выгодных зон:</b>\n\n"
            for i, zone in enumerate(nearby_zones[:3], 1):  # Show top 3
                message += (
                    f"{i}. {zone['name']}\n"
                    f"   💰 {zone['coefficient']:.1f}x | "
                    f"📏 {zone['distance']:.1f} км\n"
                )
            message += usage_info

        return message

    except Exception as e:
        print(f"Error checking geo alerts: {e}")
        return None


def add_hot_zone(name: str, latitude: float, longitude: float,
                 coefficient: float, radius_km: float = 2.0) -> bool:
    """
    Add a new hot zone to the database.

    Args:
        name: Zone name
        latitude: Zone latitude
        longitude: Zone longitude
        coefficient: Surge coefficient
        radius_km: Alert radius in kilometers

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect("taxi-botbot.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO hot_zones (name, latitude, longitude, coefficient, radius_km)
            VALUES (?, ?, ?, ?, ?)
        """, (name, latitude, longitude, coefficient, radius_km))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Error adding hot zone: {e}")
        return False


def toggle_user_alerts(user_id: int, enabled: bool) -> bool:
    """
    Enable or disable geo alerts for a user.

    Args:
        user_id: User ID
        enabled: True to enable, False to disable

    Returns:
        True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect("taxi-botbot.db")
        cursor = conn.cursor()

        # Create user_settings table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                alerts_enabled INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert or update user settings
        cursor.execute("""
            INSERT INTO user_settings (user_id, alerts_enabled)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                alerts_enabled = excluded.alerts_enabled,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, 1 if enabled else 0))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"Error toggling user alerts: {e}")
        return False
