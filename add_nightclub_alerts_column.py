#!/usr/bin/env python3
"""Add nightclub_alerts_enabled column to users table."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bot.db"

print("=" * 60)
print("ADDING NIGHTCLUB_ALERTS_ENABLED COLUMN")
print("=" * 60)
print()

if not DB_PATH.exists():
    print(f"❌ Database not found at: {DB_PATH}")
    sys.exit(1)

print(f"📁 Database: {DB_PATH}")
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("[1/3] Checking current table structure...")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

if 'nightclub_alerts_enabled' in column_names:
    print("✅ nightclub_alerts_enabled column already exists!")
    conn.close()
    sys.exit(0)

print("[2/3] Adding nightclub_alerts_enabled column...")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN nightclub_alerts_enabled BOOLEAN DEFAULT 1")
    conn.commit()
    print("  ✅ nightclub_alerts_enabled added (default: enabled)")
    print()

except Exception as e:
    print(f"❌ Error adding column: {e}")
    conn.rollback()
    conn.close()
    sys.exit(1)

print("[3/3] Verifying changes...")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

if 'nightclub_alerts_enabled' in column_names:
    print("=" * 60)
    print("✅ MIGRATION COMPLETED!")
    print("=" * 60)
    print()
    print("Next: Restart bot and update nightclub_alerts service")
else:
    print("❌ Verification failed")
    conn.close()
    sys.exit(1)

conn.close()
