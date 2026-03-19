"""Payment service - Robokassa integration for subscriptions."""
import logging
import hashlib
import json
from typing import Optional
from urllib.parse import urlencode, quote

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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

# Test price for debugging (5 rubles for 1 day pro subscription)
TEST_PRICE = 5


def get_robokassa_url(test_mode: bool = True) -> str:
    """Get Robokassa payment URL based on mode."""
    if test_mode:
        return "https://auth.robokassa.ru/Merchant/Index.aspx"
    return "https://auth.robokassa.ru/Merchant/Index.aspx"


def calculate_signature(
    merchant_login: str,
    out_sum: float,
    inv_id: int,
    password: str,
    receipt: Optional[str] = None,
    **extra_params
) -> str:
    """
    Calculate MD5 signature for Robokassa payment.

    Format: MD5(MerchantLogin:OutSum:InvId:Receipt:Password[:Shp_param1=value1:Shp_param2=value2...])

    Note: Receipt must be URL-encoded before being added to signature.
    """
    # Build signature string
    sig_parts = [
        merchant_login,
        f"{out_sum:.2f}",
        str(inv_id)
    ]

    # Add receipt if provided (for 54-FZ compliance)
    # Receipt must be URL-encoded for signature calculation
    if receipt:
        sig_parts.append(quote(receipt))

    sig_parts.append(password)

    # Add custom parameters in alphabetical order (Shp_*)
    if extra_params:
        sorted_params = sorted(extra_params.items())
        for key, value in sorted_params:
            if key.startswith("Shp_"):
                sig_parts.append(f"{key}={value}")

    sig_string = ":".join(sig_parts)
    return hashlib.md5(sig_string.encode('utf-8')).hexdigest()


def verify_result_signature(
    out_sum: str,
    inv_id: int,
    password: str,
    signature: str,
    **extra_params
) -> bool:
    """
    Verify signature from Robokassa result callback.

    Format: MD5(OutSum:InvId:Password2[:Shp_param1=value1:Shp_param2=value2...])

    Note: out_sum must be the original string from Robokassa (e.g., "5.000000")
    to match their signature calculation.
    """
    sig_parts = [
        out_sum,
        str(inv_id),
        password
    ]

    # Add custom parameters in alphabetical order (Shp_*)
    if extra_params:
        sorted_params = sorted(extra_params.items())
        for key, value in sorted_params:
            if key.startswith("Shp_"):
                sig_parts.append(f"{key}={value}")

    sig_string = ":".join(sig_parts)
    calculated_sig = hashlib.md5(sig_string.encode('utf-8')).hexdigest().upper()

    logger.info(f"Signature verification: string='{sig_string}', calculated={calculated_sig}, received={signature.upper()}")

    return calculated_sig == signature.upper()


async def create_payment(
    user_id: int,
    tier: SubscriptionTier,
    duration_days: int = 30,
    inv_id: Optional[int] = None,
    custom_amount: Optional[float] = None
) -> Optional[dict]:
    """
    Create payment URL for Robokassa.

    Args:
        user_id: User ID
        tier: Subscription tier to purchase
        duration_days: Subscription duration in days
        inv_id: Invoice ID (optional, will be generated if not provided)
        custom_amount: Custom payment amount (optional, for test payments)

    Returns:
        Payment info dict with payment_url and inv_id
    """
    if not settings.robokassa_merchant_login or not settings.robokassa_password1:
        logger.error("Robokassa not configured")
        return None

    try:
        # Use custom amount if provided, otherwise use standard price
        if custom_amount is not None:
            price = custom_amount
        else:
            price = SUBSCRIPTION_PRICES.get(tier)
            if not price:
                logger.error(f"No price configured for tier {tier}")
                return None

        # Generate invoice ID if not provided
        if inv_id is None:
            import time
            inv_id = int(time.time())

        # Custom parameters (will be returned in callback)
        custom_params = {
            "Shp_user_id": str(user_id),
            "Shp_tier": tier.value,
            "Shp_duration": str(duration_days)
        }

        # Build receipt for fiscal compliance (54-FZ)
        tier_names = {
            SubscriptionTier.PRO: "Подписка Pro",
            SubscriptionTier.PREMIUM: "Подписка Premium",
            SubscriptionTier.ELITE: "Подписка Elite"
        }

        receipt = {
            "sno": "usn_income",
            "items": [
                {
                    "name": f"{tier_names.get(tier, 'Подписка')} на {duration_days} дней",
                    "quantity": 1,
                    "sum": price,
                    "payment_method": "full_prepayment",
                    "payment_object": "service",
                    "tax": "none"
                }
            ]
        }

        receipt_json = json.dumps(receipt, ensure_ascii=False)

        # Calculate signature with receipt
        signature = calculate_signature(
            merchant_login=settings.robokassa_merchant_login,
            out_sum=price,
            inv_id=inv_id,
            password=settings.robokassa_password1,
            receipt=receipt_json,
            **custom_params
        )

        # Build payment URL
        params = {
            "MerchantLogin": settings.robokassa_merchant_login,
            "OutSum": f"{price:.2f}",
            "InvId": inv_id,
            "Description": f"Подписка {tier.value.upper()} на {duration_days} дней",
            "SignatureValue": signature,
            "Receipt": quote(receipt_json),
            "IsTest": "1" if settings.robokassa_test_mode else "0",
            **custom_params
        }

        payment_url = f"{get_robokassa_url(settings.robokassa_test_mode)}?{urlencode(params, safe=':,')}"

        logger.info(f"Created Robokassa payment for user {user_id}, tier {tier.value}, inv_id {inv_id}, receipt={receipt_json}")

        return {
            "payment_url": payment_url,
            "inv_id": inv_id,
            "amount": price,
            "tier": tier.value
        }

    except Exception as e:
        logger.error(f"Failed to create Robokassa payment: {e}")
        return None


async def process_payment_result(result_data: dict, bot=None) -> bool:
    """
    Process payment result callback from Robokassa.

    Expected parameters:
    - OutSum: payment amount
    - InvId: invoice ID
    - SignatureValue: signature
    - Shp_user_id: user ID
    - Shp_tier: subscription tier
    - Shp_duration: duration in days

    Returns:
        True if processed successfully
    """
    try:
        logger.info(f"Processing payment result: {result_data}")

        # Keep OutSum as original string for signature verification
        out_sum_str = result_data.get("OutSum", "0")
        out_sum = float(out_sum_str)
        inv_id = int(result_data.get("InvId", 0))
        signature = result_data.get("SignatureValue", "")

        # Extract custom parameters
        user_id = int(result_data.get("Shp_user_id", 0))
        tier_value = result_data.get("Shp_tier", "")
        duration_days = int(result_data.get("Shp_duration", 30))

        logger.info(f"Parsed: OutSum={out_sum}, InvId={inv_id}, user_id={user_id}, tier={tier_value}, duration={duration_days}")

        if not all([out_sum, inv_id, signature, user_id, tier_value]):
            logger.error(f"Missing required parameters: out_sum={out_sum}, inv_id={inv_id}, signature={bool(signature)}, user_id={user_id}, tier_value={tier_value}")
            return False

        # Verify signature
        custom_params = {
            "Shp_user_id": str(user_id),
            "Shp_tier": tier_value,
            "Shp_duration": str(duration_days)
        }

        logger.info(f"Verifying signature: received={signature}, custom_params={custom_params}")

        if not verify_result_signature(
            out_sum=out_sum_str,  # Pass original string, not formatted float
            inv_id=inv_id,
            password=settings.robokassa_password2,
            signature=signature,
            **custom_params
        ):
            logger.error(f"Invalid signature for payment {inv_id}. Received: {signature}")
            return False

        logger.info(f"Signature verified successfully for payment {inv_id}")

        # Convert tier string to enum
        tier = SubscriptionTier(tier_value)

        # Verify amount (allow test price of 5 rubles for 1-day subscriptions)
        expected_price = SUBSCRIPTION_PRICES.get(tier)
        is_test_payment = (abs(out_sum - TEST_PRICE) < 0.01 and duration_days == 1)

        if not is_test_payment and abs(out_sum - expected_price) > 0.01:
            logger.error(f"Amount mismatch: expected {expected_price}, got {out_sum}")
            return False

        # Use actual paid amount for test payments
        if is_test_payment:
            expected_price = TEST_PRICE
            logger.info(f"Processing test payment: {out_sum}₽ for {duration_days} day(s)")

        # Upgrade subscription
        await upgrade_subscription(
            user_id=user_id,
            tier=tier,
            duration_days=duration_days,
            payment_method="robokassa"
        )

        # Process referral earnings
        from bot.services.referral import process_subscription_payment
        await process_subscription_payment(user_id, tier, expected_price)

        # Send notification to user
        if bot:
            try:
                tier_names = {
                    "pro": "⭐ Pro",
                    "premium": "💎 Premium",
                    "elite": "👑 Elite"
                }
                tier_name = tier_names.get(tier.value, tier.value.upper())

                message = (
                    f"✅ <b>Подписка активирована!</b>\n\n"
                    f"Тариф: <b>{tier_name}</b>\n"
                    f"Сумма: <b>{expected_price}₽</b>\n"
                    f"Срок: <b>{duration_days} дней</b>\n\n"
                    f"Спасибо за покупку! 🎉"
                )

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
                ])

                await bot.send_message(user_id, message, parse_mode="HTML", reply_markup=keyboard)
                logger.info(f"Sent payment confirmation to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send payment notification to user {user_id}: {e}")
        else:
            logger.warning(f"Bot instance not available, skipping notification for user {user_id}")

        logger.info(f"Successfully processed Robokassa payment {inv_id} for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Failed to process Robokassa result: {e}")
        return False


def format_payment_info(payment_info: dict) -> str:
    """Format payment information for user."""
    tier_names = {
        "pro": "⭐ Pro",
        "premium": "💎 Premium",
        "elite": "👑 Elite"
    }

    tier_name = tier_names.get(payment_info["tier"], payment_info["tier"])
    amount = payment_info["amount"]

    test_notice = "\n\n⚠️ <b>ТЕСТОВЫЙ РЕЖИМ</b>" if settings.robokassa_test_mode else ""

    return (
        f"💳 <b>ОПЛАТА ПОДПИСКИ</b>\n\n"
        f"Тариф: {tier_name}\n"
        f"Стоимость: {amount}₽/месяц\n\n"
        f"Нажмите кнопку ниже для перехода к оплате.\n"
        f"После успешной оплаты подписка активируется автоматически.{test_notice}"
    )
