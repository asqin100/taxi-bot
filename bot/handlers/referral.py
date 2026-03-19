"""Referral system handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services import referral as ref_service
from bot.services.message_manager import send_and_cleanup
from bot.config import settings

router = Router()


@router.message(Command("referral"))
async def cmd_referral(message: Message):
    """Show referral program info and stats."""
    user_id = message.from_user.id

    # Get or create referral code
    referral_code = await ref_service.get_or_create_referral_code(user_id)

    # Get stats
    stats = await ref_service.get_referral_stats(user_id)

    if not stats:
        await send_and_cleanup(message, "❌ Ошибка получения данных")
        return

    bot_username = settings.bot_username or "KefPulse_bot"
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"

    text = (
        f"🎁 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
        f"💰 <b>Ваш баланс: {stats['balance']:.2f}₽</b>\n\n"
        f"👥 <b>Статистика:</b>\n"
        f"  Уровень 1: {stats['level_1_count']} чел.\n"
        f"  Уровень 2: {stats['level_2_count']} чел.\n"
        f"  Всего заработано: {stats['total_earned']:.2f}₽\n\n"
        f"📊 <b>Условия:</b>\n"
        f"  • 30% с подписок рефералов 1 уровня\n"
        f"  • 10% с подписок рефералов 2 уровня\n"
        f"  • +100₽ за первую оплату реферала\n\n"
        f"🎯 <b>Бонусы за количество:</b>\n"
        f"  • 5 рефералов → +200₽\n"
        f"  • 10 рефералов → +500₽\n"
        f"  • 25 рефералов → +1500₽\n"
        f"  • 50 рефералов → +5000₽\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"💡 Баланс можно использовать для оплаты подписки!"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Оплатить балансом", callback_data="referral:pay_subscription")],
        [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")],
    ])

    await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "menu:referral")
async def cb_referral_menu(callback: CallbackQuery):
    """Show referral menu from callback."""
    user_id = callback.from_user.id

    # Get or create referral code
    referral_code = await ref_service.get_or_create_referral_code(user_id)

    # Get stats
    stats = await ref_service.get_referral_stats(user_id)

    if not stats:
        await callback.answer("❌ Ошибка получения данных", show_alert=True)
        return

    bot_username = settings.bot_username or "KefPulse_bot"
    referral_link = f"https://t.me/{bot_username}?start={referral_code}"

    text = (
        f"🎁 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
        f"💰 <b>Ваш баланс: {stats['balance']:.2f}₽</b>\n\n"
        f"👥 <b>Статистика:</b>\n"
        f"  Уровень 1: {stats['level_1_count']} чел.\n"
        f"  Уровень 2: {stats['level_2_count']} чел.\n"
        f"  Всего заработано: {stats['total_earned']:.2f}₽\n\n"
        f"📊 <b>Условия:</b>\n"
        f"  • 30% с подписок рефералов 1 уровня\n"
        f"  • 10% с подписок рефералов 2 уровня\n"
        f"  • +100₽ за первую оплату реферала\n\n"
        f"🎯 <b>Бонусы за количество:</b>\n"
        f"  • 5 рефералов → +200₽\n"
        f"  • 10 рефералов → +500₽\n"
        f"  • 25 рефералов → +1500₽\n"
        f"  • 50 рефералов → +5000₽\n\n"
        f"🔗 <b>Ваша ссылка:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"💡 Баланс можно использовать для оплаты подписки!"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Оплатить балансом", callback_data="referral:pay_subscription")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "referral:pay_subscription")
async def cb_pay_with_balance(callback: CallbackQuery):
    """Show subscription payment options with referral balance."""
    user_id = callback.from_user.id
    balance = await ref_service.get_balance(user_id)

    from bot.models.subscription import SUBSCRIPTION_FEATURES, SubscriptionTier

    pro_price = SUBSCRIPTION_FEATURES[SubscriptionTier.PRO]["price"]
    premium_price = SUBSCRIPTION_FEATURES[SubscriptionTier.PREMIUM]["price"]
    elite_price = SUBSCRIPTION_FEATURES[SubscriptionTier.ELITE]["price"]

    text = (
        f"💰 <b>ОПЛАТА ПОДПИСКИ</b>\n\n"
        f"Ваш баланс: <b>{balance:.2f}₽</b>\n\n"
        f"Выберите тариф:\n\n"
        f"⭐ <b>Pro</b> — {pro_price}₽/мес\n"
        f"  • Неограниченные уведомления\n"
        f"  • AI-советник\n"
        f"  • Детальная аналитика\n\n"
        f"💎 <b>Premium</b> — {premium_price}₽/мес\n"
        f"  • Все функции Pro\n"
        f"  • Приоритетные уведомления\n"
        f"  • Персональные рекомендации\n\n"
        f"👑 <b>Elite</b> — {elite_price}₽/мес\n"
        f"  • Все функции Premium\n"
        f"  • CSV экспорт смен\n"
        f"  • Тепловая карта заработка\n"
        f"  • ML предсказания спроса"
    )

    keyboard_buttons = []

    # Show Pro button if balance is sufficient
    if balance >= pro_price:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"⭐ Pro — {pro_price}₽ (с баланса)",
                callback_data="subscription:pay_balance:pro"
            )
        ])

    # Show Premium button if balance is sufficient
    if balance >= premium_price:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"💎 Premium — {premium_price}₽ (с баланса)",
                callback_data="subscription:pay_balance:premium"
            )
        ])

    # Show Elite button if balance is sufficient
    if balance >= elite_price:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"👑 Elite — {elite_price}₽ (с баланса)",
                callback_data="subscription:pay_balance:elite"
            )
        ])

    if not keyboard_buttons:
        text += f"\n\n⚠️ Недостаточно средств на балансе.\nПригласите друзей для пополнения!"

    keyboard_buttons.append([
        InlineKeyboardButton(text="💳 Оплатить", callback_data="subscription:upgrade")
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu:referral")
    ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Removed duplicate handler - now using subscription:pay_balance: from subscription.py
# The referral program now redirects to the unified payment handler
