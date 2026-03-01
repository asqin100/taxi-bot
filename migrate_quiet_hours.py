"""Migration script to add quiet hours to User model."""
import sqlite3
from pathlib import Path

# Hardcoded database path
DB_PATH = Path(__file__).parent / "data" / "bot.db"


def migrate():
    """Add quiet hours columns to users table."""
    print(f"Migrating database: {DB_PATH}")

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        print("Run migrate_event_filters.py first to create the database")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    migrations_applied = []

    # Add quiet_hours_enabled column
    if "quiet_hours_enabled" not in columns:
        print("Adding column: quiet_hours_enabled")
        cursor.execute("ALTER TABLE users ADD COLUMN quiet_hours_enabled BOOLEAN DEFAULT 0")
        migrations_applied.append("quiet_hours_enabled")
    else:
        print("Column quiet_hours_enabled already exists")

    # Add quiet_hours_start column
    if "quiet_hours_start" not in columns:
        print("Adding column: quiet_hours_start")
        cursor.execute("ALTER TABLE users ADD COLUMN quiet_hours_start INTEGER DEFAULT 22")
        migrations_applied.append("quiet_hours_start")
    else:
        print("Column quiet_hours_start already exists")

    # Add quiet_hours_end column
    if "quiet_hours_end" not in columns:
        print("Adding column: quiet_hours_end")
        cursor.execute("ALTER TABLE users ADD COLUMN quiet_hours_end INTEGER DEFAULT 7")
        migrations_applied.append("quiet_hours_end")
    else:
        print("Column quiet_hours_end already exists")

    conn.commit()
    conn.close()

    if migrations_applied:
        print(f"\n✅ Migration complete! Added columns: {', '.join(migrations_applied)}")
    else:
        print("\n✅ No migration needed - all columns already exist")


if __name__ == "__main__":
    migrate()
