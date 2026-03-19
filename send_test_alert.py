"""Send test geo alert to user."""
import asyncio
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.config import settings

async def main():
    bot = Bot(token=settings.bot_token)

    # Test alert data
    zone_name = "Кузьминки"
    coefficient = 1.85
    tariff = "Эконом"
    distance = 2.5
    zone_lat = 55.7058
    zone_lon = 37.7658

    text = (
        f"🔥 <b>ВЫСОКИЙ КОЭФФИЦИЕНТ РЯДОМ!</b>\n\n"
        f"📍 Зона: <b>{zone_name}</b>\n"
        f"💰 Коэффициент: <b>x{coefficient}</b>\n"
        f"🚗 Тариф: {tariff}\n"
        f"📏 Расстояние: <b>{distance:.1f} км</b>\n\n"
        f"Нажмите кнопку, чтобы построить маршрут!\n\n"
        f"⚠️ <i>Это тестовое сообщение</i>"
    )

    nav_url = f"https://yandex.ru/maps/?rtext=~{zone_lat},{zone_lon}&rtt=auto"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Поехали!", url=nav_url)],
        [InlineKeyboardButton(text="🔕 Отключить геоалерты", callback_data="geo_alerts:disable")],
    ])

    try:
        await bot.send_message(
            chat_id=244638301,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        print("✅ Тестовое сообщение отправлено!")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
