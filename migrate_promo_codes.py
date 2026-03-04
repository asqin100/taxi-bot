"""Migration script to update promo_codes table with discount support."""
import asyncio
import logging
from sqlalchemy import text

from bot.database.db import get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def column_exists(session, table_name: str, column_name: str) -> bool:
    """Check if column exists in table."""
    result = await session.execute(text(f"PRAGMA table_info({table_name})"))
    columns = result.fetchall()
    return any(col[1] == column_name for col in columns)


async def migrate():
    """Add new columns to promo_codes table."""
    async with get_session() as session:
        try:
            # Add promo_type column to promo_codes
            if not await column_exists(session, "promo_codes", "promo_type"):
                await session.execute(text(
                    "ALTER TABLE promo_codes ADD COLUMN promo_type VARCHAR(20) DEFAULT 'activation'"
                ))
                logger.info("Added promo_type column to promo_codes")
            else:
                logger.info("promo_type column already exists in promo_codes")

            # Add discount columns to promo_codes
            if not await column_exists(session, "promo_codes", "discount_type"):
                await session.execute(text(
                    "ALTER TABLE promo_codes ADD COLUMN discount_type VARCHAR(20)"
                ))
                logger.info("Added discount_type column")

            if not await column_exists(session, "promo_codes", "discount_value"):
                await session.execute(text(
                    "ALTER TABLE promo_codes ADD COLUMN discount_value FLOAT"
                ))
                logger.info("Added discount_value column")

            if not await column_exists(session, "promo_codes", "applicable_tiers"):
                await session.execute(text(
                    "ALTER TABLE promo_codes ADD COLUMN applicable_tiers VARCHAR(100)"
                ))
                logger.info("Added applicable_tiers column")

            # Update promo_code_usage table
            if not await column_exists(session, "promo_code_usage", "promo_type"):
                await session.execute(text(
                    "ALTER TABLE promo_code_usage ADD COLUMN promo_type VARCHAR(20) DEFAULT 'activation'"
                ))
                logger.info("Added promo_type column to promo_code_usage")

            if not await column_exists(session, "promo_code_usage", "discount_amount"):
                await session.execute(text(
                    "ALTER TABLE promo_code_usage ADD COLUMN discount_amount FLOAT"
                ))
                logger.info("Added discount_amount column")

            if not await column_exists(session, "promo_code_usage", "original_price"):
                await session.execute(text(
                    "ALTER TABLE promo_code_usage ADD COLUMN original_price FLOAT"
                ))
                logger.info("Added original_price column")

            if not await column_exists(session, "promo_code_usage", "final_price"):
                await session.execute(text(
                    "ALTER TABLE promo_code_usage ADD COLUMN final_price FLOAT"
                ))
                logger.info("Added final_price column")

            await session.commit()
            logger.info("✅ Migration completed successfully!")
            logger.info("Note: SQLite doesn't support ALTER COLUMN, so tier and duration_days remain NOT NULL in schema but can be NULL via model")

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
