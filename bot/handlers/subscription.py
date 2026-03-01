"""Subscription handler - manage user subscriptions."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.subscription import (
    get_subscription,
    format_subscription_info,
    format_tier_comparison,
)
from bot.services.payment import create_payment, format_payment_info
from bot.models.subscription import SubscriptionTier
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
    """Handle subscription purchase."""
    tier_str = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    # Map string to enum
    tier_map = {
        "pro": SubscriptionTier.PRO,
        "premium": SubscriptionTier.PREMIUM
    }
    tier = tier_map.get(tier_str)

    if not tier:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return

    # Send "processing" message
    await callback.message.edit_text("⏳ Создаю платёж...")

    # Create payment
    payment_info = await create_payment(user_id, tier, duration_days=30)

    if not payment_info:
        # Fallback to manual payment
        text = (
            "💳 <b>ОПЛАТА ПОДПИСКИ</b>\n\n"
            f"Вы выбрали тариф: <b>{tier_str.upper()}</b>\n\n"
            "⚠️ <i>Автоматическая оплата временно недоступна.</i>\n\n"
            "Для активации подписки свяжитесь с администратором:\n"
            "@admin"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="subscription:upgrade")],
        ])
    else:
        # Show payment link
        text = format_payment_info(payment_info)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_info["confirmation_url"])],
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="subscription:upgrade")],
        ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
