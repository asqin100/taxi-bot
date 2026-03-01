"""Migration script to add tariff field to financial settings."""
import sqlite3
from pathlib import Path

# Hardcoded database path
DB_PATH = Path(__file__).parent / "data" / "bot.db"


def migrate():
    """Add tariff column to user_financial_settings table."""
    print(f"Migrating database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run other migrations first to create the database")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(user_financial_settings)")
    columns = [row[1] for row in cursor.fetchall()]

    migrations_applied = []

    # Add tariff column
    if "tariff" not in columns:
        print("Adding column: tariff")
        cursor.execute("ALTER TABLE user_financial_settings ADD COLUMN tariff VARCHAR(32) DEFAULT 'econom'")
        # Update existing rows to have default value
        cursor.execute("UPDATE user_financial_settings SET tariff = 'econom' WHERE tariff IS NULL")
        migrations_applied.append("tariff")
    else:
        print("Column tariff already exists")

    # Update commission_percent default for existing users (optional)
    # This will set commission to 18% (econom default) for users who have the old 20% default
    cursor.execute("UPDATE user_financial_settings SET commission_percent = 18.0 WHERE commission_percent = 20.0 AND tariff = 'econom'")

    conn.commit()
    conn.close()

    if migrations_applied:
        print(f"\nMigration complete! Added columns: {', '.join(migrations_applied)}")
    else:
        print("\nNo migration needed - all columns already exist")


if __name__ == "__main__":
    migrate()
