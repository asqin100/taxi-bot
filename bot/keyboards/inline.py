from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from bot.config import settings
from bot.services.zones import get_zones

TARIFF_OPTIONS = [
    ("econom", "Эконом"),
    ("comfort", "Комфорт"),
    ("business", "Бизнес"),
]

EVENT_TYPE_OPTIONS = [
    ("concert", "🎵 Концерты"),
    ("sport", "⚽ Спорт"),
    ("theater", "🎭 Театр"),
    ("conference", "🎤 Конференции"),
    ("other", "📍 Другое"),
]


BACK_BUTTON = [InlineKeyboardButton(text="◀️ Назад", callback_data="cmd:menu")]


def tariff_keyboard(selected: set[str] | None = None, has_business_access: bool = True) -> InlineKeyboardMarkup:
    selected = selected or set()
    buttons = []
    for tid, name in TARIFF_OPTIONS:
        check = "✅ " if tid in selected else ""

        # Add lock icon for Business if no access
        if tid == "business" and not has_business_access:
            name = f"{name} 🔒 Pro"

        buttons.append([InlineKeyboardButton(text=f"{check}{name}", callback_data=f"tariff:{tid}")])
    buttons.append([InlineKeyboardButton(text="Готово ✔", callback_data="tariff:done")])
    buttons.append(BACK_BUTTON)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def zones_keyboard(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    zones = get_zones()
    buttons = []
    for z in zones:
        check = "✅ " if z.id in selected else ""
        buttons.append([InlineKeyboardButton(text=f"{check}{z.name}", callback_data=f"zone:{z.id}")])
    buttons.append([InlineKeyboardButton(text="Все зоны", callback_data="zone:all")])
    buttons.append([InlineKeyboardButton(text="Готово ✔", callback_data="zone:done")])
    buttons.append(BACK_BUTTON)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def event_types_keyboard(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    buttons = []
    for tid, name in EVENT_TYPE_OPTIONS:
        check = "✅ " if tid in selected else ""
        buttons.append([InlineKeyboardButton(text=f"{check}{name}", callback_data=f"event_type:{tid}")])
    buttons.append([InlineKeyboardButton(text="Готово ✔", callback_data="event_type:done")])
    buttons.append(BACK_BUTTON)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def notify_keyboard(enabled: bool, event_notify_enabled: bool = True, quiet_hours_enabled: bool = False, geo_alerts_enabled: bool = False) -> InlineKeyboardMarkup:
    status = "🔔 Вкл" if enabled else "🔕 Выкл"
    event_status = "🔔 Вкл" if event_notify_enabled else "🔕 Выкл"
    quiet_status = "🔔 Вкл" if quiet_hours_enabled else "🔕 Выкл"
    geo_status = "🔔 Вкл" if geo_alerts_enabled else "🔕 Выкл"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Уведомления о коэффициентах: {status}", callback_data="notify:toggle")],
        [InlineKeyboardButton(text="Порог коэффициента", callback_data="notify:threshold")],
        [InlineKeyboardButton(text=f"Уведомления о мероприятиях: {event_status}", callback_data="notify:event_toggle")],
        [InlineKeyboardButton(text="Типы мероприятий", callback_data="notify:event_types")],
        [InlineKeyboardButton(text=f"📍 Геоалерты: {geo_status}", callback_data="geo_alerts:toggle")],
        [InlineKeyboardButton(text="📍 Обновить геолокацию", callback_data="geo_alerts:update_location")],
        [InlineKeyboardButton(text=f"Тихие часы: {quiet_status}", callback_data="notify:quiet_toggle")],
        [InlineKeyboardButton(text="⏰ Настроить время", callback_data="notify:quiet_hours")],
        BACK_BUTTON,
    ])


def threshold_keyboard() -> InlineKeyboardMarkup:
    values = ["1.2", "1.5", "1.8", "2.0", "2.5"]
    buttons = [[InlineKeyboardButton(text=f"x{v}", callback_data=f"threshold:{v}")] for v in values]
    buttons.append(BACK_BUTTON)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quiet_hours_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for setting quiet hours start/end time."""
    hours = list(range(24))
    buttons = []

    # Create rows of 6 hours each
    for i in range(0, 24, 6):
        row = [InlineKeyboardButton(text=f"{h:02d}:00", callback_data=f"quiet_hour:{h}") for h in hours[i:i+6]]
        buttons.append(row)

    buttons.append(BACK_BUTTON)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    if settings.webapp_url:
        buttons.append([InlineKeyboardButton(
            text="🗺 Открыть карту",
            web_app=WebAppInfo(url=settings.webapp_url),
        )])
        # Game button temporarily disabled - will be enabled later
        # buttons.append([InlineKeyboardButton(
        #     text="🎮 Игра (зарабатывай баланс!)",
        #     web_app=WebAppInfo(url=f"{settings.webapp_url}/game"),
        # )])
    buttons.extend([
        [InlineKeyboardButton(text="⚡ Все функции", callback_data="menu:features")],
        [InlineKeyboardButton(text="🏆 ТОП-5 зон", callback_data="cmd:top")],
        [InlineKeyboardButton(text="🤖 AI-советник", callback_data="menu:advisor")],
        # [InlineKeyboardButton(text="🗺 Горячие точки", callback_data="menu:hotspots")],
        [
            InlineKeyboardButton(text="💰 Финансы", callback_data="menu:financial"),
            InlineKeyboardButton(text="🚦 Пробки", callback_data="menu:traffic"),
        ],
        [
            InlineKeyboardButton(text="🔍 Поиск", callback_data="menu:search"),
            InlineKeyboardButton(text="📍 Геоалерты", callback_data="menu:geo_alerts"),
        ],
        [
            InlineKeyboardButton(text="🔔 Уведомления", callback_data="cmd:notify"),
            InlineKeyboardButton(text="🏅 Достижения", callback_data="menu:achievements"),
        ],
        [
            InlineKeyboardButton(text="🏆 Челлендж", callback_data="menu:challenge"),
            # InlineKeyboardButton(text="📊 Рейтинг", callback_data="menu:leaderboard"),  # Временно отключено
        ],
        [
            InlineKeyboardButton(text="⭐ Подписка", callback_data="menu:subscription"),
            InlineKeyboardButton(text="🎁 Реферальная программа", callback_data="menu:referral"),
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="cmd:settings"),
            InlineKeyboardButton(text="❓ Справка", callback_data="help:main"),
        ],
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def financial_menu_keyboard(has_active_shift: bool = False) -> InlineKeyboardMarkup:
    """Financial tracker menu."""
    buttons = []

    if has_active_shift:
        buttons.append([InlineKeyboardButton(text="⏹ Завершить смену", callback_data="financial:shift_end")])
    else:
        buttons.append([InlineKeyboardButton(text="▶️ Начать смену", callback_data="financial:shift_start")])

    buttons.extend([
        [InlineKeyboardButton(text="📊 Статистика", callback_data="financial:stats")],
        [InlineKeyboardButton(text="📥 Экспорт в CSV", callback_data="menu_export")],
        [
            InlineKeyboardButton(text="💸 Расходы", callback_data="financial:expenses"),
            InlineKeyboardButton(text="🎯 Цели", callback_data="financial:goals"),
        ],
        [InlineKeyboardButton(text="🚗 Мой тариф", callback_data="financial:tariff")],
        BACK_BUTTON,
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tariff_selection_keyboard(current_tariff: str = "econom") -> InlineKeyboardMarkup:
    """Keyboard for selecting driver's tariff."""
    from bot.models.financial_settings import TARIFF_NAMES, TARIFF_COMMISSIONS

    buttons = []
    for tariff_id, tariff_name in TARIFF_NAMES.items():
        commission = TARIFF_COMMISSIONS[tariff_id]
        check = "✅ " if tariff_id == current_tariff else ""
        buttons.append([
            InlineKeyboardButton(
                text=f"{check}{tariff_name} (комиссия {commission}%)",
                callback_data=f"tariff_select:{tariff_id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад к финансам", callback_data="menu:financial")])
    buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def traffic_menu_keyboard() -> InlineKeyboardMarkup:
    """Traffic conditions menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚦 Общая обстановка", callback_data="traffic:general")],
        [InlineKeyboardButton(text="🛣 МКАД", callback_data="traffic:mkad")],
        [InlineKeyboardButton(text="🔄 ТТК", callback_data="traffic:ttk")],
        BACK_BUTTON,
    ])


def search_menu_keyboard() -> InlineKeyboardMarkup:
    """Search menu with instructions."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Как использовать", callback_data="search:help")],
        BACK_BUTTON,
    ])


def subscription_keyboard() -> InlineKeyboardMarkup:
    """Subscription upgrade keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Улучшить до Pro (299₽)", callback_data="menu:subscription")],
        [InlineKeyboardButton(text="💎 Улучшить до Premium (499₽)", callback_data="menu:subscription")],
        [InlineKeyboardButton(text="👑 Улучшить до Elite (999₽)", callback_data="menu:subscription")],
        [InlineKeyboardButton(text="◀️ Назад к настройкам", callback_data="cmd:settings")],
    ])


def features_menu_keyboard(tier: str) -> InlineKeyboardMarkup:
    """Features menu based on subscription tier."""
    from bot.models.subscription import SubscriptionTier

    buttons = []

    # Basic features (available to all)
    buttons.extend([
        [InlineKeyboardButton(text="📊 Коэффициенты", callback_data="cmd:kef")],
        [InlineKeyboardButton(text="🏆 ТОП-5 зон", callback_data="cmd:top")],
        [InlineKeyboardButton(text="🔍 Поиск по адресу", callback_data="menu:search")],
    ])

    # Pro+ features
    if tier in [SubscriptionTier.PRO.value, SubscriptionTier.PREMIUM.value, SubscriptionTier.ELITE.value]:
        buttons.extend([
            [InlineKeyboardButton(text="🤖 AI-советник", callback_data="menu:advisor")],
            [InlineKeyboardButton(text="🚦 Прогноз пробок", callback_data="menu:traffic")],
            [InlineKeyboardButton(text="🔍 Поиск по адресу", callback_data="menu:search")],
        ])
    else:
        buttons.extend([
            [InlineKeyboardButton(text="🤖 AI-советник 🔒 Pro", callback_data="feature_locked:ai_advisor")],
            [InlineKeyboardButton(text="🚦 Прогноз пробок 🔒 Pro", callback_data="feature_locked:traffic")],
            [InlineKeyboardButton(text="🔍 Поиск по адресу 🔒 Pro", callback_data="feature_locked:search")],
        ])

    # Elite features
    if tier == SubscriptionTier.ELITE.value:
        buttons.extend([
            [InlineKeyboardButton(text="📥 Экспорт в CSV", callback_data="menu_export")],
            [InlineKeyboardButton(text="📊 Карта заработка", callback_data="menu_heatmap")],
            [InlineKeyboardButton(text="💰 Калькулятор налогов", callback_data="menu_tax")],
        ])
    else:
        buttons.extend([
            [InlineKeyboardButton(text="📥 Экспорт в CSV 🔒 Elite", callback_data="feature_locked:csv_export")],
            [InlineKeyboardButton(text="📊 Карта заработка 🔒 Elite", callback_data="feature_locked:heatmap")],
            [InlineKeyboardButton(text="💰 Калькулятор налогов 🔒 Elite", callback_data="feature_locked:tax")],
        ])

    buttons.append(BACK_BUTTON)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
