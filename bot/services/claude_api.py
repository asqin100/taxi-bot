"""AI API integration for advanced AI recommendations (using Google Gemini)."""
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
- Тарифы: Эконом, Комфорт, Бизнес
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
    Ask Gemini API a question with optional context.

    Args:
        question: User's question
        context: Additional context (current coefficients, traffic, etc.)

    Returns:
        Gemini's response
    """
    if not settings.gemini_api_key:
        return (
            "⚠️ AI-советник временно недоступен.\n\n"
            "Используйте базовые рекомендации через кнопку "
            "\"🤖 Где работать сейчас?\""
        )

    try:
        system_prompt = TAXI_KNOWLEDGE_BASE
        if context:
            system_prompt += f"\n\nТЕКУЩАЯ СИТУАЦИЯ:\n{context}"

        # Combine system prompt and question for Gemini
        full_prompt = f"{system_prompt}\n\n{question}"

        logger.info(f"Sending request to Gemini API (prompt length: {len(full_prompt)} chars)")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.gemini_api_key}",
                headers={
                    "content-type": "application/json",
                },
                json={
                    "contents": [{
                        "parts": [{
                            "text": full_prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 4096,
                    }
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Gemini API error: {response.status} - {error_text}")
                    return "❌ Ошибка при обращении к AI-советнику. Попробуйте позже."

                data = await response.json()
                logger.info(f"Full Gemini response: {data}")

                # Extract text from Gemini response
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]

                    # Check finish reason
                    finish_reason = candidate.get("finishReason", "UNKNOWN")
                    logger.info(f"Finish reason: {finish_reason}")

                    answer = candidate["content"]["parts"][0]["text"]
                    logger.info(f"Extracted answer length: {len(answer)} chars")
                    return answer
                else:
                    logger.error(f"Unexpected Gemini response format: {data}")
                    return "❌ Ошибка при обработке ответа. Попробуйте позже."

    except asyncio.TimeoutError:
        logger.error("Gemini API timeout")
        return "⏱ Превышено время ожидания ответа. Попробуйте позже."
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
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
