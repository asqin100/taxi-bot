"""API authentication using API keys."""
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def get_current_user(api_key: str = Security(api_key_header)) -> User:
    """
    Validate API key and return the associated user.
    API access requires active subscription with api_access feature.
    """
    async with session_factory() as session:
        # Find user by API key (stored in user model)
        result = await session.execute(
            select(User).where(User.api_key == api_key)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        # Check if user has active subscription with API access
        if not hasattr(user, 'subscription') or not user.subscription:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API access requires active subscription"
            )

        if not user.subscription.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Subscription expired"
            )

        if 'api_access' not in user.subscription.features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API access not included in your subscription plan"
            )

        # Update last API usage
        user.last_api_usage = datetime.now()
        await session.commit()

        return user
