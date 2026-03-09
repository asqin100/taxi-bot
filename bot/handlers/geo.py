"""
Handler for geolocation functionality.
"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
import sqlite3
from typing import Optional

router = Router()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard with Main Menu button."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    return keyboard


@router.message(F.content_type == 'location')
async def handle_location(message: Message) -> None:
    """
    Handle location sharing from user.
    Responds with confirmation and triggers geo alerts if enabled.
    """
    user_id = message.from_user.id
    location = message.location

    if not location:
        return

    latitude = location.latitude
    longitude = location.longitude

    try:
        # Save location to database
        conn = sqlite3.connect("taxi-botbot.db")
        cursor = conn.cursor()

        # Store user location
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_locations (
                user_id INTEGER,
                latitude REAL,
                longitude REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            INSERT INTO user_locations (user_id, latitude, longitude)
            VALUES (?, ?, ?)
        """, (user_id, latitude, longitude))

        conn.commit()

        # Check if user has geo alerts enabled
        cursor.execute("""
            SELECT alerts_enabled FROM user_settings
            WHERE user_id = ?
        """, (user_id,))

        result = cursor.fetchone()
        alerts_enabled = result[0] if result else False

        conn.close()

        # Send confirmation message
        response = (
            f"📍 <b>Местоположение получено</b>\n\n"
            f"Координаты: {latitude:.6f}, {longitude:.6f}\n"
        )

        if alerts_enabled:
            # Import and trigger geo alerts
            from bot.services.alerts import check_geo_alerts
            alert_message = await check_geo_alerts(user_id, latitude, longitude)
            if alert_message:
                response += f"\n{alert_message}"
                # Add main menu button when coefficient alert is shown
                await message.answer(response, parse_mode="HTML", reply_markup=get_main_menu_keyboard())
                return
            else:
                response += "\n✅ Уведомления о зонах активны"
        else:
            response += "\n💡 <i>Включите уведомления для получения алертов о выгодных зонах</i>"

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        await message.answer(
            "❌ Ошибка при обработке местоположения. Попробуйте позже.",
            parse_mode="HTML"
        )
        print(f"Error handling location: {e}")


@router.message(Command("geo"))
async def cmd_geo_info(message: Message) -> None:
    """
    Show information about geo features.
    """
    response = (
        "📍 <b>Геолокация</b>\n\n"
        "Поделитесь своим местоположением, чтобы:\n"
        "• Получать уведомления о выгодных зонах\n"
        "• Видеть коэффициенты рядом с вами\n"
        "• Находить зоны с высоким спросом\n\n"
        "Нажмите 📎 → Геопозиция, чтобы поделиться местоположением"
    )

    await message.answer(response, parse_mode="HTML")
