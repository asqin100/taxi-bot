"""Onboarding handler - guide new users."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.onboarding import get_onboarding_step, mark_onboarding_completed

router = Router()


@router.callback_query(F.data.startswith("onboarding:"))
async def cb_onboarding(callback: CallbackQuery):
    """Handle onboarding navigation."""
    step = callback.data.split(":")[1]
    user_id = callback.from_user.id

    # Get step data
    step_data = get_onboarding_step(step)

    text = f"{step_data['title']}\n\n{step_data['text']}"

    # Build keyboard
    buttons = []

    if step_data['next']:
        buttons.append([
            InlineKeyboardButton(text="Далее ➡️", callback_data=f"onboarding:{step_data['next']}")
        ])
    else:
        # Last step - mark as completed
        await mark_onboarding_completed(user_id)
        buttons.append([
            InlineKeyboardButton(text="🚀 Начать работу", callback_data="cmd:menu")
        ])

    # Add skip button (except on last step)
    if step != "welcome" and step_data['next']:
        buttons.append([
            InlineKeyboardButton(text="⏭ Пропустить обучение", callback_data="onboarding:skip")
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "onboarding:skip")
async def cb_onboarding_skip(callback: CallbackQuery):
    """Skip onboarding."""
    user_id = callback.from_user.id
    await mark_onboarding_completed(user_id)

    await callback.message.edit_text(
        "✅ Обучение пропущено!\n\n"
        "Вы всегда можете вернуться к справке командой /help\n\n"
        "Удачной работы! 🚕",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
        ])
    )
    await callback.answer()
