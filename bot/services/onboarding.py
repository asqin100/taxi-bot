"""Onboarding service - guide new users through bot features."""
import logging
from typing import Optional

from sqlalchemy import select

from bot.database.db import get_session
from bot.models.user import User

logger = logging.getLogger(__name__)


async def should_show_onboarding(user_id: int) -> bool:
    """Check if user should see onboarding."""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return True

        # Show onboarding if user hasn't completed it
        return not user.onboarding_completed


async def mark_onboarding_completed(user_id: int):
    """Mark onboarding as completed for user."""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.onboarding_completed = True
            await session.commit()
            logger.info(f"User {user_id} completed onboarding")


ONBOARDING_STEPS = {
    "welcome": {
        "title": "👋 Добро пожаловать!",
        "text": (
            "Привет! Я бот-помощник для водителей такси.\n\n"
            "Помогу вам:\n"
            "🔥 Находить зоны с высокими коэффициентами\n"
            "💰 Отслеживать заработок и расходы\n"
            "🚦 Следить за пробками\n"
            "🤖 Получать умные рекомендации\n"
            "🏆 Зарабатывать достижения\n\n"
            "Давайте быстро пройдемся по основным функциям!"
        ),
        "next": "coefficients"
    },
    "coefficients": {
        "title": "📊 Коэффициенты",
        "text": (
            "<b>Главная функция бота</b>\n\n"
            "Используйте команду /kef чтобы увидеть текущие коэффициенты по всем районам Москвы.\n\n"
            "🏆 /top - ТОП-5 самых жирных точек прямо сейчас\n"
            "🔍 /search &lt;адрес&gt; - узнать коэф по конкретному адресу\n\n"
            "💡 Совет: Следите за медалями 🥇🥈🥉 и огоньками 🔥🔥🔥"
        ),
        "next": "financial"
    },
    "financial": {
        "title": "💰 Финансовый трекер",
        "text": (
            "<b>Контролируйте свои финансы</b>\n\n"
            "Начните смену: /shift_start\n"
            "Завершите смену: /shift_end\n\n"
            "Бот автоматически рассчитает:\n"
            "• Расходы на топливо ⛽\n"
            "• Комиссию сервиса 💳\n"
            "• Чистый доход 💵\n"
            "• Почасовую ставку 📊\n\n"
            "Смотрите статистику: /stats"
        ),
        "next": "notifications"
    },
    "notifications": {
        "title": "🔔 Уведомления",
        "text": (
            "<b>Не пропускайте выгодные моменты</b>\n\n"
            "Настройте уведомления: /notify\n\n"
            "Получайте алерты когда:\n"
            "🔥 Коэффициент превысит порог\n"
            "🎭 Начнется концерт или матч\n"
            "🚦 Изменится дорожная обстановка\n\n"
            "💡 Настройте тихие часы, чтобы не получать уведомления ночью"
        ),
        "next": "gamification"
    },
    "gamification": {
        "title": "🏆 Геймификация",
        "text": (
            "<b>Зарабатывайте достижения!</b>\n\n"
            "🏅 Достижения: /achievements\n"
            "10 типов достижений за разные успехи\n\n"
            "🏆 Челленджи: /challenge\n"
            "Еженедельные задания с наградами\n\n"
            "📊 Рейтинг: /leaderboard\n"
            "Соревнуйтесь с другими водителями (анонимно)\n\n"
            "💡 Чем больше работаете, тем больше достижений!"
        ),
        "next": "advisor"
    },
    "advisor": {
        "title": "🤖 AI-советник",
        "text": (
            "<b>Умные рекомендации</b>\n\n"
            "AI-советник анализирует:\n"
            "• Текущие коэффициенты 📊\n"
            "• Пробки 🚦\n"
            "• Время суток ⏰\n"
            "• Вашу личную статистику 📈\n\n"
            "И подсказывает, где выгоднее работать!\n\n"
            "⭐ Доступно на тарифах Pro, Premium и Elite\n\n"
            "Команда: /advisor"
        ),
        "next": "complete"
    },
    "complete": {
        "title": "✅ Готово!",
        "text": (
            "<b>Вы готовы к работе!</b>\n\n"
            "Основные команды:\n"
            "📊 /kef - коэффициенты\n"
            "🏆 /top - лучшие зоны\n"
            "💰 /shift_start - начать смену\n"
            "🔔 /notify - настроить уведомления\n\n"
            "❓ Нужна помощь? Используйте /help\n\n"
            "Удачной работы! 🚕💨"
        ),
        "next": None
    }
}


def get_onboarding_step(step: str) -> dict:
    """Get onboarding step data."""
    return ONBOARDING_STEPS.get(step, ONBOARDING_STEPS["welcome"])
