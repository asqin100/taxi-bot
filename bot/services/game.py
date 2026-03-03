"""Game service - handle game score submissions and anti-cheat."""
import logging
import hashlib
import hmac
from datetime import datetime, timedelta
from urllib.parse import parse_qs

from sqlalchemy import select, func

from bot.config import settings
from bot.database.db import get_session
from bot.models.user import User
from bot.models.referral import ReferralEarning, EarningType

logger = logging.getLogger(__name__)

# Anti-cheat settings
MAX_SCORE_PER_GAME = 10000
MAX_GAMES_PER_HOUR = 3
POINTS_TO_RUBLES = 5 / 1000  # 1000 points = 5 rubles


def validate_telegram_init_data(init_data: str) -> dict | None:
    """
    Validate Telegram WebApp initData.
    Returns user data if valid, None otherwise.
    """
    try:
        # Parse init_data
        parsed = parse_qs(init_data)

        # Extract hash
        received_hash = parsed.get('hash', [None])[0]
        if not received_hash:
            logger.warning("No hash in initData")
            return None

        # Remove hash from data
        data_check_string_parts = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                value = parsed[key][0]
                data_check_string_parts.append(f"{key}={value}")

        data_check_string = '\n'.join(data_check_string_parts)

        # Calculate expected hash
        secret_key = hmac.new(
            "WebAppData".encode(),
            settings.bot_token.encode(),
            hashlib.sha256
        ).digest()

        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # Compare hashes
        if received_hash != expected_hash:
            logger.warning("Invalid hash in initData")
            return None

        # Extract user data
        user_data = parsed.get('user', [None])[0]
        if not user_data:
            logger.warning("No user data in initData")
            return None

        import json
        user_info = json.loads(user_data)

        return user_info

    except Exception as e:
        logger.error(f"Error validating initData: {e}")
        return None


async def submit_game_score(score: int, init_data: str) -> dict:
    """
    Submit game score and add earnings to user balance.

    Returns:
        dict with success status, balance, and optional error message
    """
    # Validate initData
    user_info = validate_telegram_init_data(init_data)
    if not user_info:
        return {"success": False, "error": "Неверные данные авторизации"}

    telegram_id = user_info.get('id')
    if not telegram_id:
        return {"success": False, "error": "Не удалось определить пользователя"}

    # Validate score
    if score < 0:
        logger.warning(f"Negative score from user {telegram_id}: {score}")
        return {"success": False, "error": "Неверный результат"}

    if score > MAX_SCORE_PER_GAME:
        logger.warning(f"Score too high from user {telegram_id}: {score}")
        return {"success": False, "error": "Подозрительно высокий результат"}

    async with get_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False, "error": "Пользователь не найден"}

        # Check rate limiting - count games in last hour (BEFORE checking score == 0)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # First, create a temporary record to reserve a slot (prevents race condition)
        temp_earning = ReferralEarning(
            user_id=user.id,
            amount=0,
            earning_type=EarningType.GAME_EARNING,
            from_user_id=None,
            subscription_tier=None,
            created_at=datetime.utcnow()  # Use UTC to match database
        )
        session.add(temp_earning)
        await session.flush()  # Write to DB but don't commit yet

        # Now count including the new record
        result = await session.execute(
            select(func.count(ReferralEarning.id))
            .where(
                ReferralEarning.user_id == user.id,
                ReferralEarning.earning_type == EarningType.GAME_EARNING,
                ReferralEarning.created_at >= one_hour_ago
            )
        )
        games_count = result.scalar()

        logger.info(f"User {telegram_id} game attempt: {games_count} games in last hour (limit: {MAX_GAMES_PER_HOUR})")

        if games_count > MAX_GAMES_PER_HOUR:
            # Rollback the temporary record
            await session.rollback()
            logger.warning(f"User {telegram_id} blocked: exceeded game limit ({games_count}/{MAX_GAMES_PER_HOUR})")
            return {
                "success": False,
                "error": f"Лимит игр: {MAX_GAMES_PER_HOUR} в час. Попробуйте позже."
            }

        # Return early for zero score (but AFTER rate limit check)
        if score == 0:
            # The temp_earning record already exists, just commit it
            await session.commit()
            return {"success": True, "balance": user.referral_balance, "earned": 0}

        # Calculate earnings
        earned_rubles = score * POINTS_TO_RUBLES

        # Update user balance
        user.referral_balance += earned_rubles

        # Update the temp_earning record with actual amount
        temp_earning.amount = earned_rubles

        await session.commit()

        logger.info(f"User {telegram_id} earned {earned_rubles}₽ from game (score: {score})")

        return {
            "success": True,
            "balance": round(user.referral_balance, 2),
            "earned": round(earned_rubles, 2)
        }
