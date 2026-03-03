"""Payment service - YooKassa integration for subscriptions."""
import logging
import uuid
from typing import Optional
from datetime import datetime, timedelta

from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotification

from bot.config import settings
from bot.models.subscription import SubscriptionTier
from bot.services.subscription import upgrade_subscription

logger = logging.getLogger(__name__)

# Subscription prices in rubles
SUBSCRIPTION_PRICES = {
    SubscriptionTier.PRO: 299,
    SubscriptionTier.PREMIUM: 499,
    SubscriptionTier.ELITE: 999,
}


def init_yookassa():
    """Initialize YooKassa configuration."""
    if settings.yookassa_shop_id and settings.yookassa_secret_key:
        Configuration.account_id = settings.yookassa_shop_id
        Configuration.secret_key = settings.yookassa_secret_key
        logger.info("YooKassa configured")
    else:
        logger.warning("YooKassa credentials not configured")


async def create_payment(
    user_id: int,
    tier: SubscriptionTier,
    duration_days: int = 30
) -> Optional[dict]:
    """
    Create payment for subscription upgrade.

    Args:
        user_id: User ID
        tier: Subscription tier to purchase
        duration_days: Subscription duration in days

    Returns:
        Payment info dict with confirmation_url and payment_id
    """
    if not settings.yookassa_shop_id:
        logger.error("YooKassa not configured")
        return None

    try:
        price = SUBSCRIPTION_PRICES.get(tier)
        if not price:
            logger.error(f"No price configured for tier {tier}")
            return None

        # Create unique idempotence key
        idempotence_key = str(uuid.uuid4())

        # Create payment
        payment = Payment.create({
            "amount": {
                "value": f"{price}.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.webapp_url or "https://t.me/KefPulse_bot"
            },
            "capture": True,
            "description": f"Подписка {tier.value.upper()} на {duration_days} дней",
            "metadata": {
                "user_id": str(user_id),
                "tier": tier.value,
                "duration_days": str(duration_days)
            }
        }, idempotence_key)

        logger.info(f"Created payment {payment.id} for user {user_id}, tier {tier.value}")

        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "amount": price,
            "tier": tier.value
        }

    except Exception as e:
        logger.error(f"Failed to create payment: {e}")
        return None


async def check_payment_status(payment_id: str) -> Optional[str]:
    """
    Check payment status.

    Args:
        payment_id: YooKassa payment ID

    Returns:
        Payment status: "pending", "succeeded", "canceled"
    """
    try:
        payment = Payment.find_one(payment_id)
        return payment.status
    except Exception as e:
        logger.error(f"Failed to check payment status: {e}")
        return None


async def process_payment_webhook(webhook_data: dict) -> bool:
    """
    Process payment webhook from YooKassa.

    Args:
        webhook_data: Webhook notification data

    Returns:
        True if processed successfully
    """
    try:
        notification = WebhookNotification(webhook_data)
        payment = notification.object

        if payment.status != "succeeded":
            logger.info(f"Payment {payment.id} status: {payment.status}")
            return False

        # Extract metadata
        user_id = int(payment.metadata.get("user_id"))
        tier = SubscriptionTier(payment.metadata.get("tier"))
        duration_days = int(payment.metadata.get("duration_days", 30))

        # Upgrade subscription
        await upgrade_subscription(
            user_id=user_id,
            tier=tier,
            duration_days=duration_days,
            payment_method="yookassa"
        )

        # Process referral earnings
        from bot.services.referral import process_subscription_payment
        price = SUBSCRIPTION_PRICES.get(tier, 0)
        await process_subscription_payment(user_id, tier, price)

        logger.info(f"Successfully processed payment {payment.id} for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        return False


def format_payment_info(payment_info: dict) -> str:
    """Format payment information for user."""
    tier_names = {
        "pro": "⭐ Pro",
        "premium": "💎 Premium"
    }

    tier_name = tier_names.get(payment_info["tier"], payment_info["tier"])
    amount = payment_info["amount"]

    return (
        f"💳 <b>ОПЛАТА ПОДПИСКИ</b>\n\n"
        f"Тариф: {tier_name}\n"
        f"Стоимость: {amount}₽/месяц\n\n"
        f"Нажмите кнопку ниже для перехода к оплате.\n"
        f"После успешной оплаты подписка активируется автоматически."
    )
