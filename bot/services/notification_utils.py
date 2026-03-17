"""Utility functions for notifications."""
from bot.models.user import User
from bot.utils.timezone import now


def is_quiet_hours(user: User) -> bool:
    """
    Check if current time is within user's quiet hours.

    Args:
        user: User object with quiet hours settings

    Returns:
        True if current time is within quiet hours, False otherwise
    """
    if not user.quiet_hours_enabled:
        return False

    current_hour = now().hour
    start = user.quiet_hours_start
    end = user.quiet_hours_end

    # Handle cases where quiet hours span midnight
    if start < end:
        # Normal case: e.g., 08:00 to 20:00
        return start <= current_hour < end
    else:
        # Spans midnight: e.g., 22:00 to 07:00
        return current_hour >= start or current_hour < end
