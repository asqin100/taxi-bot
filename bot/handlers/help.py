"""Help and tutorial system."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.message_manager import send_and_cleanup

router = Router()


HELP_SECTIONS = {
    "main": {
        "title": "📖 Справка",
        "text": (
            "Добро пожаловать в бот для водителей такси!\n\n"
            "Выберите раздел для получения подробной информации:"
        ),
        "buttons": [
            [
                InlineKeyboardButton(text="📊 Коэффициенты", callback_data="help:coefficients"),
                InlineKeyboardButton(text="💰 Финансы", callback_data="help:financial"),
            ],
            [
                InlineKeyboardButton(text="🚦 Пробки", callback_data="help:traffic"),
                InlineKeyboardButton(text="🔔 Уведомления", callback_data="help:notifications"),
            ],
            [
                InlineKeyboardButton(text="🤖 AI-советник", callback_data="help:advisor"),
                InlineKeyboardButton(text="🏆 Геймификация", callback_data="help:gamification"),
            ],
            [
                InlineKeyboardButton(text="⭐ Подписки", callback_data="help:subscription"),
                InlineKeyboardButton(text="📝 Команды", callback_data="help:commands"),
            ],
            [InlineKeyboardButton(text="⚖️ Юридическая информация", callback_data="help:legal")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
        ]
    },
    "coefficients": {
        "title": "📊 Коэффициенты",
        "text": (
            "<b>Радар коэффициентов</b>\n\n"
            "🔍 <b>Основные функции:</b>\n"
            "• /kef - текущие коэффициенты по всем районам\n"
            "• /top - ТОП-5 самых жирных точек\n"
            "• /search &lt;адрес&gt; - коэффициент по адресу\n\n"
            "🎯 <b>Фильтры:</b>\n"
            "Выбирайте тариф (Эконом, Комфорт, Бизнес) для точной информации\n\n"
            "🗺 <b>Горячие точки:</b>\n"
            "Аэропорты, вокзалы, ТЦ, стадионы - с актуальными данными и советами\n\n"
            "💡 <b>Совет:</b> Следите за медалями 🥇🥈🥉 и огоньками 🔥 - они показывают самые выгодные зоны!"
        )
    },
    "financial": {
        "title": "💰 Финансовый трекер",
        "text": (
            "<b>Управление финансами</b>\n\n"
            "▶️ <b>Начало смены:</b>\n"
            "/shift_start - начать новую смену\n\n"
            "⏹ <b>Завершение смены:</b>\n"
            "/shift_end - завершить и ввести данные:\n"
            "  • Заработок\n"
            "  • Пробег\n"
            "  • Количество поездок\n"
            "  • Аренда (если есть)\n\n"
            "📊 <b>Статистика:</b>\n"
            "/stats - статистика за день/неделю/месяц\n\n"
            "⚙️ <b>Настройки:</b>\n"
            "• /expenses - настройки расходов\n"
            "• /goal - финансовые цели\n"
            "• Выбор тарифа и комиссии\n\n"
            "💡 Бот автоматически рассчитывает расходы на топливо, комиссию и чистый доход!"
        )
    },
    "traffic": {
        "title": "🚦 Дорожная обстановка",
        "text": (
            "<b>Пробки и прогнозы</b>\n\n"
            "🚦 <b>Текущая ситуация:</b>\n"
            "/traffic - общая обстановка в Москве\n"
            "/traffic_mkad - пробки на МКАД\n"
            "/traffic_ttk - пробки на ТТК\n\n"
            "📊 <b>Прогноз:</b>\n"
            "Бот показывает прогноз пробок на ближайший час с трендом:\n"
            "  📈 Ухудшение\n"
            "  📉 Улучшение\n"
            "  ➡️ Стабильно\n\n"
            "💡 <b>Умные рекомендации:</b>\n"
            "Бот анализирует пробки + коэффициенты и дает советы, где выгоднее работать"
        )
    },
    "notifications": {
        "title": "🔔 Уведомления",
        "text": (
            "<b>Настройка алертов</b>\n\n"
            "⚙️ <b>Настройки:</b>\n"
            "/notify - открыть меню уведомлений\n\n"
            "🔥 <b>Алерты на коэффициенты:</b>\n"
            "• Выберите порог (x1.2, x1.5, x2.0...)\n"
            "• Выберите районы\n"
            "• Выберите тарифы\n"
            "• Получайте мгновенные уведомления!\n\n"
            "🎭 <b>Алерты на события:</b>\n"
            "• Концерты, матчи, театр\n"
            "• Уведомления за час до начала\n\n"
            "🌙 <b>Тихие часы:</b>\n"
            "Настройте время, когда не хотите получать уведомления"
        )
    },
    "advisor": {
        "title": "🤖 AI-советник",
        "text": (
            "<b>Умные рекомендации</b>\n\n"
            "⭐ <b>Доступ:</b> Pro, Premium и Elite подписки\n\n"
            "🧠 <b>Что анализирует:</b>\n"
            "• Текущие коэффициенты\n"
            "• Дорожная обстановка\n"
            "• Время суток и день недели\n"
            "• Вашу личную статистику\n\n"
            "📊 <b>Персональные инсайты:</b>\n"
            "• Ваши лучшие часы работы\n"
            "• Ваши лучшие дни недели\n"
            "• Сравнение с вашей средней ставкой\n\n"
            "💡 <b>Использование:</b>\n"
            "/advisor - получить рекомендацию\n\n"
            "Чем больше смен вы завершите, тем точнее будут рекомендации!"
        )
    },
    "gamification": {
        "title": "🏆 Геймификация",
        "text": (
            "<b>Достижения и рейтинги</b>\n\n"
            "🏅 <b>Достижения:</b>\n"
            "/achievements - 10 типов достижений\n"
            "• Первая смена, Ночная сова, Марафонец\n"
            "• Миллионер, Мастер коэффициентов\n"
            "• Автоматическая разблокировка\n\n"
            "🏆 <b>Еженедельные челленджи:</b>\n"
            "/challenge - текущий челлендж\n"
            "• 7 типов: заработок, смены, часы, поездки\n"
            "• 3 уровня сложности\n"
            "• Награды за выполнение\n\n"
            "📊 <b>Рейтинг:</b>\n"
            "/leaderboard - анонимный рейтинг\n"
            "• По заработку, часам, эффективности\n"
            "• Фильтры: неделя, месяц\n"
            "• Все имена анонимны 🔒"
        )
    },
    "subscription": {
        "title": "⭐ Подписки",
        "text": (
            "<b>Тарифные планы</b>\n\n"
            "🆓 <b>Free (бесплатно):</b>\n"
            "• Базовые коэффициенты\n"
            "• ТОП-5 зон\n"
            "• 3 уведомления\n"
            "• Финансовый трекер\n\n"
            "⭐ <b>Pro (299₽/мес):</b>\n"
            "• Всё из Free\n"
            "• AI-советник\n"
            "• Безлимитные уведомления\n"
            "• Прогноз пробок\n\n"
            "💎 <b>Premium (499₽/мес):</b>\n"
            "• Всё из Pro\n"
            "• Приоритетная поддержка\n"
            "• Ранний доступ к новым функциям\n"
            "• Расширенная аналитика\n\n"
            "👑 <b>Elite (999₽/мес):</b>\n"
            "• Всё из Premium\n"
            "• Выгрузка смен для налоговой (безлимит)\n"
            "• Карта заработка: когда выгоднее работать\n"
            "• Статистика за месяц\n"
            "• Прогноз спроса на 24 часа вперёд\n"
            "• Автоматический расчёт налогов для самозанятых\n\n"
            "💡 Улучшить тариф: /subscription"
        )
    },
    "commands": {
        "title": "📝 Список команд",
        "text": (
            "<b>Основные команды</b>\n\n"
            "📊 <b>Коэффициенты:</b>\n"
            "/kef - текущие коэффициенты\n"
            "/top - ТОП-5 зон\n"
            "/search &lt;адрес&gt; - поиск по адресу\n\n"
            "💰 <b>Финансы:</b>\n"
            "/shift_start - начать смену\n"
            "/shift_end - завершить смену\n"
            "/stats - статистика\n"
            "/expenses - настройки расходов\n"
            "/goal - финансовые цели\n\n"
            "🚦 <b>Пробки:</b>\n"
            "/traffic - общая обстановка\n"
            "/traffic_mkad - МКАД\n"
            "/traffic_ttk - ТТК\n\n"
            "🔔 <b>Уведомления:</b>\n"
            "/notify - настройки\n\n"
            "🏆 <b>Геймификация:</b>\n"
            "/achievements - достижения\n"
            "/challenge - челлендж\n"
            "/leaderboard - рейтинг\n\n"
            "🤖 <b>AI-советник:</b>\n"
            "/advisor - рекомендация\n\n"
            "⚙️ <b>Прочее:</b>\n"
            "/settings - настройки\n"
            "/subscription - подписка\n"
            "/help - эта справка"
        )
    },
    "legal": {
        "title": "⚖️ Юридическая информация",
        "text": (
            "<b>Документы и реквизиты</b>\n\n"
            "📄 <b>Юридические документы:</b>\n"
            "• Публичная оферта\n"
            "• Политика конфиденциальности\n"
            "• Политика возврата средств\n\n"
            "👤 <b>Реквизиты продавца:</b>\n"
            "СМЗ Манченко Александр Александрович\n"
            "ИНН: 301508489913\n\n"
            "📧 <b>Контакты:</b>\n"
            "Email: yotabro15@yandex.ru\n"
            "Телефон: 89822203464\n\n"
            "Нажмите на кнопки ниже, чтобы открыть документы:"
        )
    }
}


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Show help menu."""
    await _send_help(message, "main")


@router.callback_query(F.data.startswith("help:"))
async def cb_help(callback: CallbackQuery):
    """Handle help section navigation."""
    section = callback.data.split(":")[1]
    await _send_help(callback.message, section, edit=True)
    await callback.answer()


async def _send_help(message: Message, section: str = "main", edit: bool = False):
    """Send help section."""
    help_data = HELP_SECTIONS.get(section, HELP_SECTIONS["main"])

    text = f"{help_data['title']}\n\n{help_data['text']}"

    # Build keyboard
    if section == "main":
        keyboard = InlineKeyboardMarkup(inline_keyboard=help_data["buttons"])
    elif section == "legal":
        # Special keyboard for legal section with document links
        from bot.config import settings
        from aiogram.types import WebAppInfo

        oferta_url = f"{settings.webapp_url}/oferta.html" if settings.webapp_url else "#"
        privacy_url = f"{settings.webapp_url}/privacy_policy.html" if settings.webapp_url else "#"
        refund_url = f"{settings.webapp_url}/refund_policy.html" if settings.webapp_url else "#"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Публичная оферта", web_app=WebAppInfo(url=oferta_url))],
            [InlineKeyboardButton(text="🔒 Политика конфиденциальности", web_app=WebAppInfo(url=privacy_url))],
            [InlineKeyboardButton(text="↩️ Политика возврата", web_app=WebAppInfo(url=refund_url))],
            [InlineKeyboardButton(text="◀️ Назад к разделам", callback_data="help:main")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")],
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к разделам", callback_data="help:main")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")],
        ])

    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
