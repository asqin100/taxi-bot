#!/usr/bin/env python3
"""Comprehensive fix for all missing columns in users table."""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "bot.db"

print("=" * 60)
print("COMPREHENSIVE FIX: USERS TABLE")
print("=" * 60)
print()

if not DB_PATH.exists():
    print(f"❌ Database not found at: {DB_PATH}")
    sys.exit(1)

print(f"📁 Database: {DB_PATH}")
print()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("[1/4] Checking current table structure...")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"Current columns ({len(column_names)}): {', '.join(column_names)}")
print()

# Define all required columns with their types and defaults
required_columns = {
    'preferred_tariff': ('VARCHAR(64)', None),
    'geo_alerts_sent_today': ('INTEGER', '0'),
    'geo_alerts_reset_date': ('DATE', None),
}

missing_columns = []
for col_name in required_columns:
    if col_name not in column_names:
        missing_columns.append(col_name)

if not missing_columns:
    print("✅ All required columns already exist!")
    print("No migration needed.")
    conn.close()
    sys.exit(0)

print(f"[2/4] Found {len(missing_columns)} missing columns:")
for col in missing_columns:
    print(f"  - {col}")
print()

print("[3/4] Adding missing columns...")

try:
    for col_name in missing_columns:
        col_type, default_value = required_columns[col_name]

        if default_value:
            sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type} DEFAULT {default_value}"
        else:
            sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"

        print(f"  Adding {col_name}...")
        cursor.execute(sql)
        print(f"  ✅ {col_name} added")

    conn.commit()
    print()
    print("✅ All columns added successfully!")

except Exception as e:
    print(f"❌ Error adding columns: {e}")
    conn.rollback()
    conn.close()
    sys.exit(1)

print()
print("[4/4] Verifying changes...")
cursor.execute("PRAGMA table_info(users)")
columns = cursor.fetchall()
column_names = [col[1] for col in columns]

print(f"New columns count: {len(column_names)}")
print()

# Verify all required columns are present
all_present = all(col in column_names for col in required_columns)

if all_present:
    print("=" * 60)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("All required columns are now present:")
    for col in required_columns:
        print(f"  ✅ {col}")
    print()
    print("Next steps:")
    print("1. Restart the bot: systemctl restart taxibot")
    print("2. Wait 5 seconds for startup")
    print("3. Check logs: tail -100 bot.log | grep -i error")
else:
    print("❌ Verification failed - not all columns were added")
    missing = [col for col in required_columns if col not in column_names]
    print(f"Still missing: {', '.join(missing)}")
    conn.close()
    sys.exit(1)

conn.close()
