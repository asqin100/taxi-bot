"""Location sharing and geo alerts handlers."""

from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(F.location)
async def handle_location(message: Message):
    """Handle location sharing from user (both one-time and live updates)."""
    location = message.location
    user_id = message.from_user.id

    # Check if this is a live location update
    is_live = location.live_period is not None if hasattr(location, 'live_period') else False

    if not is_live:
        # ONE-TIME LOCATION: "Куда ехать?" feature
        # Search for high coefficient zones within 10 km, don't save to database
        from bot.services.yandex_api import get_cached_coefficients, generate_yandex_navigator_link, generate_yandex_maps_link
        from bot.services.zones import find_nearest_high_coefficient_zone

        surge_data = get_cached_coefficients()

        if surge_data:
            # Try to find a high coefficient zone within 10 km
            zone_result = find_nearest_high_coefficient_zone(
                user_lat=location.latitude,
                user_lon=location.longitude,
                surge_data=surge_data,
                min_coefficient=1.3,
                max_distance_km=10.0,  # 10 km for "where to go"
                tariff="econom"
            )

            if zone_result:
                # Found a zone! Show navigation options
                navigator_link = generate_yandex_navigator_link(
                    zone_result.zone.lat,
                    zone_result.zone.lon
                )
                maps_link = generate_yandex_maps_link(
                    zone_result.zone.lat,
                    zone_result.zone.lon
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🚗 Яндекс Навигатор", url=navigator_link)],
                    [InlineKeyboardButton(text="🗺 Яндекс Карты", url=maps_link)],
                    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")]
                ])

                await message.answer(
                    f"✅ <b>Найдена зона с высоким коэффициентом!</b>\n\n"
                    f"📍 <b>Зона:</b> {zone_result.zone.name}\n"
                    f"💰 <b>Коэффициент:</b> {zone_result.coefficient:.2f}x\n"
                    f"📏 <b>Расстояние:</b> {zone_result.distance_km:.1f} км\n\n"
                    f"Выберите приложение для навигации:",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                return
            else:
                # No zone found within 10 km
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")]
                ])

                await message.answer(
                    "😔 <b>Высокий коэффициент не найден</b>\n\n"
                    "К сожалению, в радиусе 10 км от вас нет зон "
                    "с коэффициентом ≥ 1.3.\n\n"
                    "💡 <i>Попробуйте позже или переместитесь в другой район</i>",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                return

    # LIVE LOCATION: Save to database for geo alerts feature
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("❌ Пользователь не найден. Используйте /start")
            return

        user.last_latitude = location.latitude
        user.last_longitude = location.longitude
        user.last_location_update = datetime.now()

        # If live location, set expiration time
        if is_live and hasattr(location, 'live_period'):
            user.live_location_expires_at = datetime.now() + timedelta(seconds=location.live_period)

        # Auto-enable geo alerts if not already enabled (and user has access)
        alerts_just_enabled = False
        if not user.geo_alerts_enabled:
            # Check subscription access
            from bot.services.subscription import check_feature_access
            has_access = await check_feature_access(user_id, "geo_alerts")

            if has_access:
                user.geo_alerts_enabled = True
                alerts_just_enabled = True

        await session.commit()

        # Always send confirmation when location is received
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
        ])

        if alerts_just_enabled:
            # First time enabling - detailed message
            await send_and_cleanup(
                message,
                "✅ <b>Live Location активирована!</b>\n\n"
                "📍 Ваше местоположение отслеживается в реальном времени\n"
                "🔔 Геоалерты включены\n\n"
                "Теперь вы будете получать уведомления о высоких коэффициентах рядом с вами!\n\n"
                "💡 <b>Как это работает:</b>\n"
                "• Бот проверяет зоны с высоким кэфом каждые 2 минуты\n"
                "• Если зона в радиусе 7 км — вы получите алерт\n"
                "• Кнопка 'Поехали' откроет навигацию в Яндекс.Картах\n\n"
                "⏱ Live Location активна на 8 часов. За 30 минут до окончания придет напоминание.",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        elif user.geo_alerts_enabled:
            # Alerts already enabled - brief confirmation
            await message.answer(
                "✅ <b>Местоположение обновлено</b>\n\n"
                f"📍 {location.latitude:.6f}, {location.longitude:.6f}\n"
                "🔔 Геоалерты активны\n\n"
                "Продолжаю отслеживать высокие коэффициенты рядом с вами.",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        else:
            # No access to geo alerts - save location but inform about feature
            await message.answer(
                "✅ <b>Местоположение сохранено</b>\n\n"
                f"📍 {location.latitude:.6f}, {location.longitude:.6f}\n\n"
                "💡 Геоалерты доступны на тарифах <b>Pro</b>, <b>Premium</b> и <b>Elite</b>.\n\n"
                "С геоалертами вы будете получать уведомления о высоких коэффициентах в радиусе 7 км от вас!",
                reply_markup=keyboard,
                parse_mode="HTML",
            )


@router.message(F.edited_message & F.edited_message.location)
async def handle_location_update(message: Message):
    """Handle live location updates (edited messages)."""
    # Silently update location without sending confirmation
    location = message.location
    user_id = message.from_user.id

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.last_latitude = location.latitude
            user.last_longitude = location.longitude
            user.last_location_update = datetime.now()
            await session.commit()


@router.callback_query(F.data == "menu:geo_alerts")
async def cb_geo_alerts_menu(callback: CallbackQuery):
    """Show geo alerts menu."""
    user_id = callback.from_user.id

    # Check subscription access
    from bot.services.subscription import check_feature_access
    has_access = await check_feature_access(user_id, "geo_alerts")

    if not has_access:
        text = (
            "📍 <b>ГЕОАЛЕРТЫ</b>\n\n"
            "⭐ Эта функция доступна только на тарифах <b>Pro</b>, <b>Premium</b> и <b>Elite</b>.\n\n"
            "Геоалерты автоматически находят высокие коэффициенты рядом с вами:\n"
            "  • Отслеживание в радиусе <b>5 км</b>\n"
            "  • Проверка каждые 2 минуты\n"
            "  • Навигация одним кликом\n"
            "  • Уведомления о выгодных зонах поблизости\n\n"
            "Улучшите тариф, чтобы получить доступ!"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬆️ Улучшить тариф", callback_data="subscription:upgrade")],
            [InlineKeyboardButton(text="◀️ Мой кабинет", callback_data="menu:profile")],
        ])
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        location_str = "не установлена"
        if user.last_latitude and user.last_longitude:
            location_str = f"{user.last_latitude:.4f}, {user.last_longitude:.4f}"
            if user.live_location_expires_at:
                expires_in = (user.live_location_expires_at - datetime.now()).total_seconds() / 3600
                if expires_in > 0:
                    location_str += f"\n⏱ Истекает через {expires_in:.1f}ч"

        status_emoji = "🔔" if user.geo_alerts_enabled else "🔕"
        status_text = "включены" if user.geo_alerts_enabled else "выключены"

        text = (
            f"📍 <b>ГЕОАЛЕРТЫ</b>\n\n"
            f"Статус: {status_emoji} <b>{status_text}</b>\n"
            f"Локация: {location_str}\n"
            f"Радиус поиска: <b>5 км</b>\n"
            f"Порог коэффициента: x{user.surge_threshold}\n\n"
            f"💡 <b>Как это работает:</b>\n"
            f"• Бот проверяет зоны с высоким кэфом каждые 2 минуты\n"
            f"• Если зона в радиусе <b>5 км</b> — вы получите алерт\n"
            f"• Кнопка 'Поехали' откроет навигацию в Яндекс.Картах\n\n"
            f"⏱ Live Location работает 8 часов. За 30 минут до окончания придет напоминание."
        )

        keyboard_buttons = []

        if user.geo_alerts_enabled:
            keyboard_buttons.append([InlineKeyboardButton(text="🔕 Отключить геоалерты", callback_data="geo_alerts:disable")])
        else:
            keyboard_buttons.append([InlineKeyboardButton(text="🔔 Включить геоалерты", callback_data="geo_alerts:enable")])

        keyboard_buttons.append([InlineKeyboardButton(text="⚙️ Изменить порог коэффициента", callback_data="geo_alerts:threshold")])
        keyboard_buttons.append([InlineKeyboardButton(text="📍 Обновить Live Location", callback_data="geo_alerts:update_location")])
        keyboard_buttons.append([InlineKeyboardButton(text="◀️ Мой кабинет", callback_data="menu:profile")])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()


@router.callback_query(F.data == "geo_alerts:enable")
async def cb_enable_geo_alerts(callback: CallbackQuery):
    """Enable geo alerts and request live location."""
    # Check subscription access
    from bot.services.subscription import check_feature_access

    user_id = callback.from_user.id
    has_access = await check_feature_access(user_id, "geo_alerts")

    if not has_access:
        text = (
            "📍 <b>ГЕОАЛЕРТЫ</b>\n\n"
            "⭐ Эта функция доступна только на тарифах <b>Pro</b> и <b>Premium</b>.\n\n"
            "Геоалерты автоматически находят высокие коэффициенты рядом с вами:\n"
            "  • Отслеживание в радиусе 7 км\n"
            "  • Проверка каждые 2 минуты\n"
            "  • Навигация одним кликом\n\n"
            "Улучшите тариф, чтобы получить доступ!"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬆️ Улучшить тариф", callback_data="subscription:upgrade")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:geo_alerts")],
        ])
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("⚠️ Требуется Pro, Premium или Elite", show_alert=True)
        return

    instruction_text = (
        "📍 <b>LIVE ГЕОЛОКАЦИЯ</b>\n\n"
        "🎯 <b>Зачем это нужно?</b>\n"
        "Бот будет автоматически находить высокие коэффициенты рядом с вами и присылать алерты с кнопкой навигации.\n\n"
        "💰 <b>Как это работает:</b>\n"
        "• Каждые 2 минуты бот проверяет зоны в радиусе <b>5 км</b> от вас\n"
        "• Если коэффициент выше порога — вы получаете уведомление\n"
        "• Нажимаете 'Поехали' → открывается маршрут в Яндекс.Картах\n\n"
        "⏱ <b>Длительность:</b>\n"
        "Live Location работает 8 часов (максимум Telegram). За 30 минут до окончания придет напоминание о продлении.\n\n"
        "🔒 <b>Конфиденциальность:</b>\n"
        "Ваша геолокация используется только для поиска выгодных зон. Данные не передаются третьим лицам.\n\n"
        "👇 Нажмите кнопку ниже, чтобы начать:"
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Включить Live Location (8 часов)", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await callback.message.answer(instruction_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "geo_alerts:threshold")
async def cb_geo_alerts_threshold(callback: CallbackQuery):
    """Show threshold selection for geo alerts."""
    user_id = callback.from_user.id

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        text = (
            "⚙️ <b>ПОРОГ КОЭФФИЦИЕНТА</b>\n\n"
            f"Текущий порог: <b>x{user.surge_threshold}</b>\n\n"
            "Выберите минимальный коэффициент для получения геоалертов:\n\n"
            "💡 Геоалерты работают в радиусе <b>5 км</b> от вашей позиции."
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="x1.2", callback_data="geo_threshold:1.2")],
            [InlineKeyboardButton(text="x1.5", callback_data="geo_threshold:1.5")],
            [InlineKeyboardButton(text="x1.8", callback_data="geo_threshold:1.8")],
            [InlineKeyboardButton(text="x2.0", callback_data="geo_threshold:2.0")],
            [InlineKeyboardButton(text="x2.5", callback_data="geo_threshold:2.5")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:geo_alerts")],
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()


@router.callback_query(F.data.startswith("geo_threshold:"))
async def cb_set_geo_threshold(callback: CallbackQuery):
    """Set threshold for geo alerts."""
    threshold = float(callback.data.split(":")[-1])
    user_id = callback.from_user.id

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one()
        user.surge_threshold = threshold
        await session.commit()

    await callback.answer(f"✅ Порог установлен: x{threshold}")

    # Return to geo alerts menu
    await cb_geo_alerts_menu(callback)



@router.callback_query(F.data == "geo_alerts:disable")
async def cb_disable_geo_alerts(callback: CallbackQuery):
    """Disable geo alerts."""
    user_id = callback.from_user.id

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one()
        user.geo_alerts_enabled = False
        user.live_location_expires_at = None
        await session.commit()

    await callback.answer("🔕 Геоалерты отключены")

    # Return to geo alerts menu
    await cb_geo_alerts_menu(callback)


@router.callback_query(F.data == "geo_alerts:toggle")
async def cb_toggle_geo_alerts(callback: CallbackQuery):
    """Toggle geo alerts on/off."""
    user_id = callback.from_user.id

    # Check subscription access when enabling
    from bot.services.subscription import check_feature_access

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one()

        if not user.geo_alerts_enabled:
            # Check if user has access before enabling
            has_access = await check_feature_access(user_id, "geo_alerts")
            if not has_access:
                await callback.answer("⚠️ Геоалерты доступны только на Pro и Premium", show_alert=True)
                return
            # Enabling - check if location is set
            if user.last_latitude is None or user.last_longitude is None:
                # Need to request location first
                await callback.answer("Сначала включите Live Location", show_alert=True)

                instruction_text = (
                    "📍 <b>LIVE ГЕОЛОКАЦИЯ</b>\n\n"
                    "🎯 <b>Зачем это нужно?</b>\n"
                    "Бот будет автоматически находить высокие коэффициенты рядом с вами и присылать алерты с кнопкой навигации.\n\n"
                    "💰 <b>Как это работает:</b>\n"
                    "• Каждые 2 минуты бот проверяет зоны в радиусе 7 км от вас\n"
                    "• Если коэффициент выше порога — вы получаете уведомление\n"
                    "• Нажимаете 'Поехали' → открывается маршрут в Яндекс.Картах\n\n"
                    "⏱ <b>Длительность:</b>\n"
                    "Live Location работает 8 часов (максимум Telegram). За 30 минут до окончания придет напоминание о продлении.\n\n"
                    "🔒 <b>Конфиденциальность:</b>\n"
                    "Ваша геолокация используется только для поиска выгодных зон. Данные не передаются третьим лицам.\n\n"
                    "👇 Нажмите кнопку ниже, чтобы начать:"
                )

                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📍 Включить Live Location (8 часов)", request_location=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True,
                )
                await callback.message.answer(instruction_text, reply_markup=keyboard, parse_mode="HTML")
                return

            user.geo_alerts_enabled = True
            await session.commit()
            await callback.answer("✅ Геоалерты включены")
        else:
            user.geo_alerts_enabled = False
            user.live_location_expires_at = None
            await session.commit()
            await callback.answer("🔕 Геоалерты отключены")

    # Refresh the notifications menu
    from bot.handlers.notifications import _get_user
    from bot.keyboards.inline import notify_keyboard

    user = await _get_user(user_id)
    event_types = user.event_types.split(",") if user.event_types else []
    event_types_str = ", ".join(event_types) if event_types else "не выбраны"

    quiet_hours_str = "выключены"
    if user.quiet_hours_enabled:
        quiet_hours_str = f"с {user.quiet_hours_start:02d}:00 до {user.quiet_hours_end:02d}:00"

    location_str = "не установлена"
    if user.last_latitude and user.last_longitude:
        location_str = f"{user.last_latitude:.4f}, {user.last_longitude:.4f}"
        if user.live_location_expires_at:
            expires_in = (user.live_location_expires_at - datetime.now()).total_seconds() / 3600
            if expires_in > 0:
                location_str += f" (истекает через {expires_in:.1f}ч)"

    await callback.message.edit_text(
        f"🔔 <b>Настройки уведомлений</b>\n\n"
        f"📊 Коэффициенты: {'включены' if user.notify_enabled else 'выключены'}\n"
        f"   Порог: x{user.surge_threshold}\n\n"
        f"🎭 Мероприятия: {'включены' if user.event_notify_enabled else 'выключены'}\n"
        f"   Типы: {event_types_str}\n\n"
        f"📍 Геоалерты: {'включены' if user.geo_alerts_enabled else 'выключены'}\n"
        f"   Локация: {location_str}\n\n"
        f"🌙 Тихие часы: {quiet_hours_str}",
        reply_markup=notify_keyboard(
            user.notify_enabled,
            user.event_notify_enabled,
            user.quiet_hours_enabled,
            user.geo_alerts_enabled,
        ),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "geo_alerts:update_location")
async def cb_update_location(callback: CallbackQuery):
    """Request location update."""
    # Check subscription access
    from bot.services.subscription import check_feature_access

    user_id = callback.from_user.id
    has_access = await check_feature_access(user_id, "geo_alerts")

    if not has_access:
        await callback.answer("⚠️ Геоалерты доступны только на Pro и Premium", show_alert=True)
        return

    instruction_text = (
        "📍 <b>ОБНОВЛЕНИЕ LIVE LOCATION</b>\n\n"
        "Включите Live Location на 8 часов, чтобы получать актуальные алерты о высоких коэффициентах рядом с вами.\n\n"
        "💡 Бот будет автоматически отслеживать ваше перемещение и присылать уведомления, когда рядом (в радиусе <b>5 км</b>) появится выгодная зона."
    )

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Обновить Live Location (8 часов)", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await callback.message.answer(instruction_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


