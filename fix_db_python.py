#!/usr/bin/env python3
"""Fix database schema using Python sqlite3."""
import sqlite3
import sys

def fix_database():
    """Add missing columns to users table."""
    try:
        conn = sqlite3.connect('data/bot.db')
        cursor = conn.cursor()

        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        changes_made = False

        # Add geo_alerts_sent_today if missing
        if 'geo_alerts_sent_today' not in columns:
            print("Adding geo_alerts_sent_today column...")
            cursor.execute("ALTER TABLE users ADD COLUMN geo_alerts_sent_today INTEGER DEFAULT 0")
            changes_made = True
        else:
            print("✓ geo_alerts_sent_today already exists")

        # Add geo_alerts_reset_date if missing
        if 'geo_alerts_reset_date' not in columns:
            print("Adding geo_alerts_reset_date column...")
            cursor.execute("ALTER TABLE users ADD COLUMN geo_alerts_reset_date TEXT")
            changes_made = True
        else:
            print("✓ geo_alerts_reset_date already exists")

        if changes_made:
            conn.commit()
            print("\n✓ Database updated successfully")
        else:
            print("\n✓ Database schema is up to date")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = fix_database()
    sys.exit(0 if success else 1)
