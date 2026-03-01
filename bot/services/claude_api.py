"""Claude API integration for advanced AI recommendations."""
import asyncio
import logging
from typing import Optional
import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)

TAXI_KNOWLEDGE_BASE = """
Ты - эксперт-советник для водителей такси в Москве. Твоя задача - давать практические советы.

КОНТЕКСТ:
- Работа в Яндекс.Такси в Москве и МО
- Коэффициенты спроса (surge pricing) от 1.0 до 5.0+
- Тарифы: Эконом, Комфорт, Комфорт+, Бизнес
- Основные зоны: аэропорты, вокзалы, ТЦ, стадионы
- Пиковые часы: утро (7-10), вечер (17-20), ночь (пт-сб 23-03)

ПРАВИЛА РАБОТЫ В ТАКСИ:
1. Лицензия: обязательна лицензия такси (выдается ГИБДД)
2. Документы: водительское удостоверение, СТС, лицензия, путевой лист
3. Штрафы за работу без лицензии: 5000₽ для водителя, 50000₽ для владельца авто
4. Требования к авто: не старше 10 лет, техосмотр, ОСАГО
5. Медосмотр: обязателен перед каждой сменой (можно онлайн)

ЧАСТЫЕ ВОПРОСЫ:
- Штрафы: работа без лицензии, превышение скорости, парковка
- Оптимизация заработка: выбор зон, время работы, тарифы
- Расходы: бензин (~15₽/км), аренда авто (1500-3000₽/день), комиссия (20-25%)
- Безопасность: отказ от подозрительных заказов, видеорегистратор

СТИЛЬ ОТВЕТОВ:
- Конкретно и по делу
- С цифрами и примерами
- Дружелюбно, но профессионально
- Эмодзи для наглядности
"""


async def ask_claude(question: str, context: Optional[str] = None) -> str:
    """
    Ask Claude API a question with optional context.

    Args:
        question: User's question
        context: Additional context (current coefficients, traffic, etc.)

    Returns:
        Claude's response
    """
    if not settings.anthropic_api_key:
        return (
            "⚠️ AI-советник временно недоступен.\n\n"
            "Используйте базовые рекомендации через кнопку "
            "\"🤖 Где работать сейчас?\""
        )

    try:
        system_prompt = TAXI_KNOWLEDGE_BASE
        if context:
            system_prompt += f"\n\nТЕКУЩАЯ СИТУАЦИЯ:\n{context}"

        messages = [
            {
                "role": "user",
                "content": question
            }
        ]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1024,
                    "system": system_prompt,
                    "messages": messages,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Claude API error: {response.status} - {error_text}")
                    return "❌ Ошибка при обращении к AI-советнику. Попробуйте позже."

                data = await response.json()
                answer = data["content"][0]["text"]

                return answer

    except asyncio.TimeoutError:
        logger.error("Claude API timeout")
        return "⏱ Превышено время ожидания ответа. Попробуйте позже."
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return "❌ Произошла ошибка. Попробуйте позже."


async def get_advanced_recommendation(
    user_id: int,
    coefficients_data: str,
    traffic_data: str,
    user_stats: Optional[str] = None
) -> str:
    """
    Get advanced recommendation using Claude API.

    Args:
        user_id: User ID
        coefficients_data: Current coefficients summary
        traffic_data: Current traffic situation
        user_stats: User's personal statistics

    Returns:
        Detailed recommendation
    """
    context = f"""
КОЭФФИЦИЕНТЫ:
{coefficients_data}

ПРОБКИ:
{traffic_data}
"""

    if user_stats:
        context += f"\n\nСТАТИСТИКА ВОДИТЕЛЯ:\n{user_stats}"

    question = (
        "Проанализируй текущую ситуацию и дай развернутую рекомендацию: "
        "где лучше работать прямо сейчас и почему? "
        "Учти коэффициенты, пробки и время суток. "
        "Ответ должен быть структурированным с конкретными зонами и обоснованием."
    )

    return await ask_claude(question, context)
