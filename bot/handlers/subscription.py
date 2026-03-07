"""Subscription handler - manage user subscriptions."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot.config import settings
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
        [InlineKeyboardButton(text="🎁 Ввести промокод", callback_data="subscription:promo")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "subscription:compare")
async def cb_subscription_compare(callback: CallbackQuery):
    """Show comparison of all subscription tiers."""
    text = format_tier_comparison()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬆️ Улучшить тариф", callback_data="subscription:upgrade")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:subscription")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
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
        "  • Поддержка 24/7\n\n"
        "👑 <b>Elite</b> — 999₽/мес\n"
        "  • Все функции Premium\n"
        "  • Выгрузка смен для налоговой\n"
        "  • Карта: когда выгоднее работать\n"
        "  • Прогноз спроса на завтра\n"
        "  • Автоматический расчёт налогов\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>Условия подписки:</b>\n"
        "  • Срок: 30 дней\n"
        "  • Автопродление: нет\n"
        "  • Отмена: в любой момент\n"
        "  • Возврат: в течение 7 дней при неиспользовании\n\n"
        "📄 <b>Реквизиты продавца:</b>\n"
        "СМЗ Манченко Александр Александрович\n"
        "ИНН: 301508489913\n"
        "📧 yotabro15@yandex.ru\n"
        "📞 89822203464"
    )

    # Build document URLs
    oferta_url = f"{settings.webapp_url}/oferta.html" if settings.webapp_url else "#"
    privacy_url = f"{settings.webapp_url}/privacy_policy.html" if settings.webapp_url else "#"
    refund_url = f"{settings.webapp_url}/refund_policy.html" if settings.webapp_url else "#"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Публичная оферта", web_app=WebAppInfo(url=oferta_url))],
        [InlineKeyboardButton(text="🔒 Политика конфиденциальности", web_app=WebAppInfo(url=privacy_url))],
        [InlineKeyboardButton(text="↩️ Политика возврата", web_app=WebAppInfo(url=refund_url))],
        [InlineKeyboardButton(text="🧪 ТЕСТ — 5₽ (1 день)", callback_data="subscription:buy:test")],
        [InlineKeyboardButton(text="⭐ Pro — 299₽/мес", callback_data="subscription:buy:pro")],
        [InlineKeyboardButton(text="💎 Premium — 499₽/мес", callback_data="subscription:buy:premium")],
        [InlineKeyboardButton(text="👑 Elite — 999₽/мес", callback_data="subscription:buy:elite")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:subscription")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("subscription:buy:"))
async def cb_subscription_buy(callback: CallbackQuery):
    """Handle subscription purchase."""
    tier_str = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    # Handle test payment (5 rubles for 1 day)
    if tier_str == "test":
        # Get user balance
        from bot.database.db import session_factory
        from bot.models.user import User
        from sqlalchemy import select

        async with session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            balance = user.referral_balance if user else 0

        # Build payment options for test
        text = (
            "💳 <b>ТЕСТОВЫЙ ПЛАТЕЖ</b>\n\n"
            "Тариф: <b>PRO (тест)</b>\n"
            "Стоимость: <b>5₽</b>\n"
            "Срок: <b>1 день</b>\n\n"
            f"💰 Ваш баланс: <b>{balance:.2f}₽</b>\n\n"
            "⚠️ Это тестовый платеж для проверки системы оплаты.\n"
            "После оплаты вы получите Pro подписку на 1 день.\n\n"
            "Выберите способ оплаты:"
        )

        keyboard_buttons = []

        # Add balance payment option if user has enough
        if balance >= 5:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"💰 Оплатить балансом (5₽)",
                    callback_data=f"subscription:pay_balance:test"
                )
            ])

        # Create payment with custom price
        from bot.config import settings
        if settings.payment_provider == "robokassa":
            from bot.services.payment_robokassa import create_payment as create_robokassa_payment
            payment_info = await create_robokassa_payment(user_id, SubscriptionTier.PRO, duration_days=1)
            # Override price to 5 rubles
            if payment_info:
                payment_url = payment_info.get("payment_url", "")
                # Replace price in URL
                payment_url = payment_url.replace("OutSum=299.00", "OutSum=5.00")
                payment_url = payment_url.replace("Description=%D0%9F%D0%BE%D0%B4%D0%BF%D0%B8%D1%81%D0%BA%D0%B0+PRO+%D0%BD%D0%B0+30+%D0%B4%D0%BD%D0%B5%D0%B9", "Description=%D0%A2%D0%B5%D1%81%D1%82+PRO+1+%D0%B4%D0%B5%D0%BD%D1%8C")
                # Recalculate signature for 5 rubles
                from bot.services.payment_robokassa import calculate_signature
                import time
                inv_id = int(time.time())
                custom_params = {
                    "Shp_user_id": str(user_id),
                    "Shp_tier": "pro",
                    "Shp_duration": "1"
                }
                signature = calculate_signature(
                    merchant_login=settings.robokassa_merchant_login,
                    out_sum=5.0,
                    inv_id=inv_id,
                    password=settings.robokassa_password1,
                    **custom_params
                )
                from urllib.parse import urlencode
                params = {
                    "MerchantLogin": settings.robokassa_merchant_login,
                    "OutSum": "5.00",
                    "InvId": inv_id,
                    "Description": "Тест PRO 1 день",
                    "SignatureValue": signature,
                    "IsTest": "0" if not settings.robokassa_test_mode else "1",
                    **custom_params
                }
                from bot.services.payment_robokassa import get_robokassa_url
                payment_url = f"{get_robokassa_url(settings.robokassa_test_mode)}?{urlencode(params)}"

                keyboard_buttons.append([
                    InlineKeyboardButton(text="💳 Оплатить картой (5₽)", url=payment_url)
                ])

        oferta_url = f"{settings.webapp_url}/oferta.html" if settings.webapp_url else "#"
        keyboard_buttons.append([InlineKeyboardButton(text="📄 Публичная оферта", web_app=WebAppInfo(url=oferta_url))])
        keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="subscription:upgrade")])
        keyboard_buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return

    # Map string to enum
    tier_map = {
        "pro": SubscriptionTier.PRO,
        "premium": SubscriptionTier.PREMIUM,
        "elite": SubscriptionTier.ELITE
    }
    tier = tier_map.get(tier_str)

    if not tier:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return

    # Get user balance
    from bot.database.db import session_factory
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        balance = user.referral_balance if user else 0

    # Get tier price
    from bot.models.subscription import SUBSCRIPTION_FEATURES
    tier_price = SUBSCRIPTION_FEATURES[tier]["price"]

    # Build payment options
    text = (
        "💳 <b>ОПЛАТА ПОДПИСКИ</b>\n\n"
        f"Тариф: <b>{tier_str.upper()}</b>\n"
        f"Стоимость: <b>{tier_price}₽/мес</b>\n\n"
        f"💰 Ваш баланс: <b>{balance:.2f}₽</b>\n\n"
        "Выберите способ оплаты:"
    )

    keyboard_buttons = []

    # Add balance payment option if user has enough
    if balance >= tier_price:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"💰 Оплатить балансом ({tier_price}₽)",
                callback_data=f"subscription:pay_balance:{tier_str}"
            )
        ])

    # Create payment based on configured provider
    from bot.config import settings

    if settings.payment_provider == "robokassa":
        from bot.services.payment_robokassa import create_payment as create_robokassa_payment
        payment_info = await create_robokassa_payment(user_id, tier, duration_days=30)
    else:
        # Default to YooKassa
        payment_info = await create_payment(user_id, tier, duration_days=30)

    if payment_info:
        # Robokassa uses payment_url, YooKassa uses confirmation_url
        payment_url = payment_info.get("payment_url") or payment_info.get("confirmation_url")
        if payment_url:
            keyboard_buttons.append([
                InlineKeyboardButton(text="💳 Оплатить картой", url=payment_url)
            ])

    oferta_url = f"{settings.webapp_url}/oferta.html" if settings.webapp_url else "#"
    keyboard_buttons.append([InlineKeyboardButton(text="📄 Публичная оферта", web_app=WebAppInfo(url=oferta_url))])
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="subscription:upgrade")])
    keyboard_buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("subscription:pay_balance:"))
async def cb_subscription_pay_balance(callback: CallbackQuery):
    """Pay for subscription using balance."""
    tier_str = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    # Handle test payment
    if tier_str == "test":
        from bot.database.db import session_factory
        from bot.models.user import User
        from bot.models.referral import ReferralEarning, EarningType
        from sqlalchemy import select
        from bot.services.subscription import upgrade_subscription

        tier_price = 5.0
        tier = SubscriptionTier.PRO
        duration_days = 1

        async with session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            if user.referral_balance < tier_price:
                await callback.answer("❌ Недостаточно средств на балансе", show_alert=True)
                return

            # Deduct from balance
            user.referral_balance -= tier_price

            # Create withdrawal record
            withdrawal = ReferralEarning(
                user_id=user.id,
                amount=-tier_price,
                earning_type=EarningType.WITHDRAWAL,
                from_user_id=None,
                subscription_tier="test"
            )
            session.add(withdrawal)
            await session.commit()

        # Upgrade subscription
        await upgrade_subscription(user_id, tier, duration_days=duration_days, payment_method="balance")

        await callback.message.edit_text(
            f"✅ <b>Тестовая подписка активирована!</b>\n\n"
            f"Тариф: <b>PRO (тест)</b>\n"
            f"Оплачено с баланса: <b>{tier_price}₽</b>\n"
            f"Остаток баланса: <b>{user.referral_balance:.2f}₽</b>\n\n"
            f"Подписка действует {duration_days} день.\n\n"
            f"Спасибо за покупку! 🎉",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
            ])
        )
        await callback.answer("✅ Подписка активирована!")
        return

    # Map string to enum
    tier_map = {
        "pro": SubscriptionTier.PRO,
        "premium": SubscriptionTier.PREMIUM,
        "elite": SubscriptionTier.ELITE
    }
    tier = tier_map.get(tier_str)

    if not tier:
        await callback.answer("❌ Неверный тариф", show_alert=True)
        return

    from bot.database.db import session_factory
    from bot.models.user import User
    from bot.models.referral import ReferralEarning, EarningType
    from sqlalchemy import select
    from bot.models.subscription import SUBSCRIPTION_FEATURES
    from bot.services.subscription import upgrade_subscription

    tier_price = SUBSCRIPTION_FEATURES[tier]["price"]

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        if user.referral_balance < tier_price:
            await callback.answer("❌ Недостаточно средств на балансе", show_alert=True)
            return

        # Deduct from balance
        user.referral_balance -= tier_price

        # Create withdrawal record
        withdrawal = ReferralEarning(
            user_id=user.id,
            amount=-tier_price,
            earning_type=EarningType.WITHDRAWAL,
            from_user_id=None,
            subscription_tier=tier_str
        )
        session.add(withdrawal)

        await session.commit()

    # Upgrade subscription
    await upgrade_subscription(user_id, tier, duration_days=30, payment_method="balance")

    await callback.message.edit_text(
        f"✅ <b>Подписка активирована!</b>\n\n"
        f"Тариф: <b>{tier_str.upper()}</b>\n"
        f"Оплачено с баланса: <b>{tier_price}₽</b>\n"
        f"Остаток баланса: <b>{user.referral_balance:.2f}₽</b>\n\n"
        f"Подписка действует 30 дней.\n\n"
        f"Спасибо за покупку! 🎉",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
        ])
    )
    await callback.answer("✅ Подписка активирована!")
