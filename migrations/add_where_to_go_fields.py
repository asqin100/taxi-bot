"""Add where_to_go tracking fields to users table."""
import sqlite3
from pathlib import Path


def migrate():
    """Add where_to_go_requests_today and where_to_go_reset_date fields to users table."""
    db_path = Path(__file__).parent.parent / "data" / "bot.db"

    print(f"Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add where_to_go_requests_today column
        if "where_to_go_requests_today" not in columns:
            print("  Adding where_to_go_requests_today column...")
            cursor.execute("ALTER TABLE users ADD COLUMN where_to_go_requests_today INTEGER DEFAULT 0")
            print("Added where_to_go_requests_today column")
        else:
            print("  where_to_go_requests_today column already exists")

        # Add where_to_go_reset_date column
        if "where_to_go_reset_date" not in columns:
            print("  Adding where_to_go_reset_date column...")
            cursor.execute("ALTER TABLE users ADD COLUMN where_to_go_reset_date TIMESTAMP")
            print("Added where_to_go_reset_date column")
        else:
            print("  where_to_go_reset_date column already exists")

        conn.commit()
        print("\nMigration completed successfully")

    except Exception as e:
        print(f"\nMigration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
