"""Promo code handler - allow users to activate promo codes."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup

from bot.services.promo_code import activate_promo_code

router = Router()


class PromoCodeStates(StatesGroup):
    """States for promo code activation."""
    waiting_for_code = State()
    choosing_tier = State()


@router.callback_query(F.data == "subscription:promo")
async def cb_promo_code_menu(callback: CallbackQuery, state: FSMContext):
    """Show promo code input prompt."""
    text = (
        "🎁 <b>АКТИВАЦИЯ ПРОМОКОДА</b>\n\n"
        "Введите промокод для активации подписки:\n\n"
        "💡 Промокоды можно получить:\n"
        "  • В нашем канале @kefpulsechannel\n"
        "  • На специальных акциях\n"
        "  • От партнёров\n\n"
        "Введите код:"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="menu:subscription")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(PromoCodeStates.waiting_for_code)
    await callback.answer()


@router.message(PromoCodeStates.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext):
    """Process entered promo code."""
    code = message.text.strip().upper()

    # Validate and activate
    success, result_message, promo = await activate_promo_code(code, message.from_user.id)

    if not success:
        # Error - show retry options
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Попробовать снова", callback_data="subscription:promo")
        builder.button(text="◀️ Назад", callback_data="menu:subscription")
        builder.adjust(1)

        await message.answer(result_message, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.clear()
        return

    if promo and promo.promo_type == "discount":
        # Discount promo - show tier selection
        await state.update_data(promo_code=code)
        await state.set_state(PromoCodeStates.choosing_tier)

        # Build tier selection keyboard
        tier_prices = {
            "pro": 299,
            "premium": 499,
            "elite": 999
        }
        tier_names = {
            "pro": "⭐ Pro",
            "premium": "💎 Premium",
            "elite": "👑 Elite"
        }

        builder = InlineKeyboardBuilder()
        applicable_tiers = promo.get_applicable_tiers()

        for tier in applicable_tiers:
            original_price = tier_prices.get(tier, 0)
            discount = promo.calculate_discount(original_price)
            final_price = promo.get_final_price(original_price)

            button_text = f"{tier_names.get(tier, tier)} - {int(final_price)}₽ (было {int(original_price)}₽)"
            builder.button(text=button_text, callback_data=f"promo:apply:{tier}")

        builder.button(text="❌ Отмена", callback_data="menu:subscription")
        builder.adjust(1)

        await message.answer(result_message, reply_markup=builder.as_markup(), parse_mode="HTML")

    else:
        # Activation promo - already activated
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Мои подписки", callback_data="menu:subscription")
        builder.button(text="🏠 Главное меню", callback_data="cmd:menu")
        builder.adjust(1)

        await message.answer(result_message, reply_markup=builder.as_markup(), parse_mode="HTML")
        await state.clear()


@router.callback_query(F.data.startswith("promo:apply:"))
async def cb_apply_discount(callback: CallbackQuery, state: FSMContext):
    """Apply discount promo to selected tier."""
    tier = callback.data.split(":")[-1]
    data = await state.get_data()
    code = data.get("promo_code")

    if not code:
        await callback.answer("❌ Промокод не найден", show_alert=True)
        await state.clear()
        return

    # Store promo info for payment
    await state.update_data(promo_code=code, promo_tier=tier)

    # TODO: Integrate with payment system
    # For now, show info message
    text = (
        f"💳 <b>Оплата со скидкой</b>\n\n"
        f"Тариф: <b>{tier}</b>\n"
        f"Промокод: <b>{code}</b>\n\n"
        f"⚠️ Интеграция с платёжной системой в разработке.\n"
        f"Промокод сохранён и будет применён при оплате."
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data="menu:subscription")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()
    await callback.answer()
