"""Migration script to add referral system fields to users table."""
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path(__file__).parent / "data" / "bot.db"


def migrate():
    """Add referral system columns to users table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add referral_code column
        cursor.execute("ALTER TABLE users ADD COLUMN referral_code VARCHAR(16)")
        logger.info("Added referral_code column")
    except sqlite3.OperationalError as e:
        logger.warning(f"referral_code column might already exist: {e}")

    try:
        # Add referrer_id column
        cursor.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER")
        logger.info("Added referrer_id column")
    except sqlite3.OperationalError as e:
        logger.warning(f"referrer_id column might already exist: {e}")

    try:
        # Add referral_balance column
        cursor.execute("ALTER TABLE users ADD COLUMN referral_balance FLOAT DEFAULT 0.0")
        logger.info("Added referral_balance column")
    except sqlite3.OperationalError as e:
        logger.warning(f"referral_balance column might already exist: {e}")

    try:
        # Update existing rows to have 0.0 balance
        cursor.execute("UPDATE users SET referral_balance = 0.0 WHERE referral_balance IS NULL")
        logger.info(f"Updated {cursor.rowcount} existing users with default balance")
    except Exception as e:
        logger.warning(f"Could not update existing rows: {e}")

    try:
        # Create index on referral_code
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_referral_code ON users (referral_code)")
        logger.info("Created index on referral_code")
    except Exception as e:
        logger.warning(f"Index might already exist: {e}")

    try:
        # Create index on referrer_id
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_referrer_id ON users (referrer_id)")
        logger.info("Created index on referrer_id")
    except Exception as e:
        logger.warning(f"Index might already exist: {e}")

    conn.commit()
    conn.close()

    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    migrate()
