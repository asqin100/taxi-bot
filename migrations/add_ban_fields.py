"""Add ban fields to users table."""
import sqlite3
from pathlib import Path


def migrate():
    """Add is_banned, ban_reason, banned_at fields to users table."""
    db_path = Path(__file__).parent.parent / "data" / "bot.db"

    print(f"📁 Using database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add is_banned column
        if "is_banned" not in columns:
            print("  Adding is_banned column...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0")
            print("✅ Added is_banned column")
        else:
            print("⏭️  is_banned column already exists")

        # Add ban_reason column
        if "ban_reason" not in columns:
            print("  Adding ban_reason column...")
            cursor.execute("ALTER TABLE users ADD COLUMN ban_reason TEXT")
            print("✅ Added ban_reason column")
        else:
            print("⏭️  ban_reason column already exists")

        # Add banned_at column
        if "banned_at" not in columns:
            print("  Adding banned_at column...")
            cursor.execute("ALTER TABLE users ADD COLUMN banned_at TIMESTAMP")
            print("✅ Added banned_at column")
        else:
            print("⏭️  banned_at column already exists")

        conn.commit()
        print("\n✅ Migration completed successfully")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
