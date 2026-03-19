#!/usr/bin/env python3
"""Fix database schema - add missing columns"""
import sqlite3
import sys
from pathlib import Path

def fix_database():
    # Find database file
    db_paths = [
        'taxi_bot.db',
        'bot.db',
        'data/taxi_bot.db',
        'data/bot.db',
    ]

    db_path = None
    for path in db_paths:
        if Path(path).exists():
            db_path = path
            break

    if not db_path:
        print("❌ Database file not found!")
        print("Searching in current directory...")
        for p in Path('.').rglob('*.db'):
            print(f"  Found: {p}")
            if 'taxi' in str(p).lower() or 'bot' in str(p).lower():
                db_path = str(p)
                break

    if not db_path:
        print("❌ Could not find database file")
        return False

    print(f"📁 Using database: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        print(f"✓ Found {len(columns)} columns in users table")

        # Add missing columns
        added = []

        if 'geo_alerts_sent_today' not in columns:
            print("  Adding geo_alerts_sent_today...")
            cursor.execute("ALTER TABLE users ADD COLUMN geo_alerts_sent_today INTEGER DEFAULT 0")
            added.append('geo_alerts_sent_today')

        if 'geo_alerts_reset_date' not in columns:
            print("  Adding geo_alerts_reset_date...")
            cursor.execute("ALTER TABLE users ADD COLUMN geo_alerts_reset_date DATETIME")
            added.append('geo_alerts_reset_date')

        conn.commit()
        conn.close()

        if added:
            print(f"✅ Added columns: {', '.join(added)}")
        else:
            print("✅ All columns already exist")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_database()
    sys.exit(0 if success else 1)
