"""Script to clear where_to_go usage for a specific user."""
import asyncio
from sqlalchemy import select, delete

from bot.database.db import session_factory, init_db
from bot.models.where_to_go_usage import WhereToGoUsage


async def clear_user_usage(username: str):
    """Clear where_to_go usage for user by username."""
    await init_db()

    # Get user ID from username
    from bot.models.user import User

    async with session_factory() as session:
        # Find user by username
        result = await session.execute(
            select(User).where(User.username == username.lstrip('@'))
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"User {username} not found")
            return

        user_id = user.telegram_id
        print(f"Found user: {username} (ID: {user_id})")

        # Delete all where_to_go usage records
        result = await session.execute(
            delete(WhereToGoUsage).where(WhereToGoUsage.user_id == user_id)
        )
        await session.commit()

        deleted_count = result.rowcount
        print(f"Deleted {deleted_count} usage records for user {username}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python clear_user_usage.py @username")
        sys.exit(1)

    username = sys.argv[1]
    asyncio.run(clear_user_usage(username))
