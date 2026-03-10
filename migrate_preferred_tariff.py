#!/usr/bin/env python3
"""Add preferred_tariff column to users table"""
import sqlite3
import sys
from pathlib import Path

def migrate_database():
    # Find database file
    db_paths = [
        'data/bot.db',
        'bot.db',
    ]

    db_path = None
    for path in db_paths:
        if Path(path).exists():
            db_path = path
            break

    if not db_path:
        print("❌ Database file not found!")
        return False

    print(f"📁 Using database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'preferred_tariff' not in columns:
            print("  Adding preferred_tariff column...")
            cursor.execute("ALTER TABLE users ADD COLUMN preferred_tariff VARCHAR(20) DEFAULT 'econom'")
            conn.commit()
            print("✅ Added preferred_tariff column")
        else:
            print("✅ preferred_tariff column already exists")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
