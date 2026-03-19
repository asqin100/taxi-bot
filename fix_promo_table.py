"""Fix promo_codes table by recreating it with correct schema."""
import asyncio
import logging
from sqlalchemy import text

from bot.database.db import get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_table():
    """Recreate promo_codes table with nullable columns."""
    async with get_session() as session:
        try:
            # Drop old tables
            await session.execute(text("DROP TABLE IF EXISTS promo_code_usage"))
            await session.execute(text("DROP TABLE IF EXISTS promo_codes"))
            logger.info("Dropped old tables")

            # Create new promo_codes table with correct schema
            await session.execute(text("""
                CREATE TABLE promo_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    promo_type VARCHAR(20) DEFAULT 'activation',
                    tier VARCHAR(20),
                    duration_days INTEGER,
                    discount_type VARCHAR(20),
                    discount_value FLOAT,
                    applicable_tiers VARCHAR(100),
                    max_uses INTEGER,
                    current_uses INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    valid_from DATETIME DEFAULT CURRENT_TIMESTAMP,
                    valid_until DATETIME,
                    created_by BIGINT,
                    description VARCHAR(200),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("Created new promo_codes table")

            # Create index
            await session.execute(text(
                "CREATE INDEX ix_promo_codes_code ON promo_codes (code)"
            ))

            # Create promo_code_usage table
            await session.execute(text("""
                CREATE TABLE promo_code_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    promo_code_id INTEGER NOT NULL,
                    user_id BIGINT NOT NULL,
                    promo_type VARCHAR(20) DEFAULT 'activation',
                    tier VARCHAR(20),
                    duration_days INTEGER,
                    discount_amount FLOAT,
                    original_price FLOAT,
                    final_price FLOAT,
                    used_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("Created promo_code_usage table")

            # Create indexes
            await session.execute(text(
                "CREATE INDEX ix_promo_code_usage_promo_code_id ON promo_code_usage (promo_code_id)"
            ))
            await session.execute(text(
                "CREATE INDEX ix_promo_code_usage_user_id ON promo_code_usage (user_id)"
            ))

            await session.commit()
            logger.info("✅ Tables recreated successfully!")
            logger.info("Note: Old promo codes were removed. Please recreate them in admin panel.")

        except Exception as e:
            logger.error(f"❌ Fix failed: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(fix_table())
