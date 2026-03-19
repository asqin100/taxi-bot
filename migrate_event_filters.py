"""Migration script to add event notification filters to User model."""
import sqlite3
from pathlib import Path

# Hardcoded database path
DB_PATH = Path(__file__).parent / "data" / "bot.db"


def migrate():
    """Add event notification columns to users table."""
    print(f"Migrating database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Create the database first by running the bot or other migrations")
        return

    conn = sqlite3.connect(str(DB_PATH))

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    migrations_applied = []

    # Add event_notify_enabled column
    if "event_notify_enabled" not in columns:
        print("Adding column: event_notify_enabled")
        cursor.execute("ALTER TABLE users ADD COLUMN event_notify_enabled BOOLEAN DEFAULT 1")
        migrations_applied.append("event_notify_enabled")
    else:
        print("Column event_notify_enabled already exists")

    # Add event_types column
    if "event_types" not in columns:
        print("Adding column: event_types")
        cursor.execute("ALTER TABLE users ADD COLUMN event_types VARCHAR(128) DEFAULT 'concert,sport'")
        # Update existing rows to have default value
        cursor.execute("UPDATE users SET event_types = 'concert,sport' WHERE event_types IS NULL")
        migrations_applied.append("event_types")
    else:
        print("Column event_types already exists")

    conn.commit()
    conn.close()

    if migrations_applied:
        print(f"\n✅ Migration complete! Added columns: {', '.join(migrations_applied)}")
    else:
        print("\n✅ No migration needed - all columns already exist")


if __name__ == "__main__":
    migrate()
