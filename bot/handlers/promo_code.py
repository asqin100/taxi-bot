"""Promo code handler - allow users to activate promo codes."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.promo_code import activate_promo_code

router = Router()


class PromoCodeStates(StatesGroup):
    """States for promo code activation."""
    waiting_for_code = State()


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
    success, result_message = await activate_promo_code(code, message.from_user.id)

    builder = InlineKeyboardBuilder()
    if success:
        builder.button(text="✅ Мои подписки", callback_data="menu:subscription")
        builder.button(text="🏠 Главное меню", callback_data="cmd:menu")
    else:
        builder.button(text="🔄 Попробовать снова", callback_data="subscription:promo")
        builder.button(text="◀️ Назад", callback_data="menu:subscription")

    builder.adjust(1)

    await message.answer(result_message, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()
