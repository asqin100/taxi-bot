"""Subscription handler - manage user subscriptions."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.subscription import (
    get_subscription,
    format_subscription_info,
    format_tier_comparison,
)
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.callback_query(F.data == "menu:subscription")
async def cb_subscription_menu(callback: CallbackQuery):
    """Show subscription menu."""
    subscription = await get_subscription(callback.from_user.id)
    text = format_subscription_info(subscription)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data="subscription:compare")],
        [InlineKeyboardButton(text="⬆️ Улучшить тариф", callback_data="subscription:upgrade")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "subscription:compare")
async def cb_subscription_compare(callback: CallbackQuery):
    """Show comparison of all subscription tiers."""
    text = format_tier_comparison()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Улучшить тариф", callback_data="subscription:upgrade")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:subscription")],
    ])

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "subscription:upgrade")
async def cb_subscription_upgrade(callback: CallbackQuery):
    """Show upgrade options."""
    text = (
        "⬆️ <b>УЛУЧШИТЬ ТАРИФ</b>\n\n"
        "Выберите тариф:\n\n"
        "⭐ <b>Pro</b> — 299₽/мес\n"
        "  • Неограниченные уведомления\n"
        "  • AI-советник\n"
        "  • Детальная аналитика\n\n"
        "💎 <b>Premium</b> — 499₽/мес\n"
        "  • Все функции Pro\n"
        "  • Приоритетные уведомления\n"
        "  • Персональные рекомендации\n"
        "  • Поддержка 24/7"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Pro — 299₽/мес", callback_data="subscription:buy:pro")],
        [InlineKeyboardButton(text="💎 Premium — 499₽/мес", callback_data="subscription:buy:premium")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:subscription")],
    ])

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("subscription:buy:"))
async def cb_subscription_buy(callback: CallbackQuery):
    """Handle subscription purchase (placeholder for payment integration)."""
    tier = callback.data.split(":")[-1]

    text = (
        "💳 <b>ОПЛАТА ПОДПИСКИ</b>\n\n"
        f"Вы выбрали тариф: <b>{tier.upper()}</b>\n\n"
        "⚠️ <i>Интеграция с платёжной системой в разработке.</i>\n\n"
        "Для активации подписки свяжитесь с администратором:\n"
        "@admin"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="subscription:upgrade")],
    ])

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
